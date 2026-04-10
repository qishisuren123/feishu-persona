"""
飞书人格基因分析机器人 - 主应用
接收飞书事件 → 拉取聊天记录 → Claude 分析 → 返回人格基因卡片
"""

import os
import json
import logging
import hashlib
import threading
from flask import Flask, request, jsonify
from feishu_client import FeishuClient
from analyzer import PersonaAnalyzer
from card_builder import CardBuilder

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化组件
feishu = FeishuClient(
    app_id=os.environ.get('FEISHU_APP_ID', ''),
    app_secret=os.environ.get('FEISHU_APP_SECRET', ''),
)
analyzer = PersonaAnalyzer(
    api_key=os.environ.get('ANTHROPIC_API_KEY', ''),
    model=os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
)
card_builder = CardBuilder()

# 已处理的事件去重
processed_events = set()


@app.route('/webhook/event', methods=['POST'])
def handle_event():
    """飞书事件订阅回调"""
    payload = request.json
    logger.info(f"Received event: {json.dumps(payload, ensure_ascii=False)[:500]}")

    # 1. URL 验证 (首次配置事件订阅时飞书发送)
    if payload.get('type') == 'url_verification':
        return jsonify({'challenge': payload.get('challenge', '')})

    # 2. v2 schema 事件处理
    schema = payload.get('schema')
    if schema == '2.0':
        header = payload.get('header', {})
        event_id = header.get('event_id', '')
        event_type = header.get('event_type', '')

        # 去重
        if event_id in processed_events:
            return jsonify({'code': 0})
        processed_events.add(event_id)
        # 防止内存泄漏，限制大小
        if len(processed_events) > 10000:
            processed_events.clear()

        # 处理消息事件
        if event_type == 'im.message.receive_v1':
            event = payload.get('event', {})
            # 异步处理，立即返回 200 给飞书
            threading.Thread(target=handle_message, args=(event,), daemon=True).start()

        return jsonify({'code': 0})

    # 3. v1 schema 兼容
    if 'event' in payload and payload.get('type') != 'url_verification':
        event = payload['event']
        threading.Thread(target=handle_message_v1, args=(event,), daemon=True).start()
        return jsonify({'code': 0})

    return jsonify({'code': 0})


def handle_message(event: dict):
    """处理 v2 消息事件"""
    try:
        sender = event.get('sender', {}).get('sender_id', {})
        sender_open_id = sender.get('open_id', '')
        message = event.get('message', {})
        chat_id = message.get('chat_id', '')
        msg_type = message.get('message_type', '')
        content_str = message.get('content', '{}')

        # 只处理文本消息
        if msg_type != 'text':
            return

        content = json.loads(content_str)
        text = content.get('text', '').strip()

        # 去掉 @机器人 的部分
        # 飞书 @机器人 格式: @_user_1 分析我
        import re
        text = re.sub(r'@_user_\d+', '', text).strip()

        logger.info(f"Message from {sender_open_id} in {chat_id}: {text}")

        # 命令路由
        if '分析我' in text or '分析自己' in text:
            do_analyze(chat_id, sender_open_id, target_open_id=sender_open_id)
        elif text.startswith('分析') and '@' not in text:
            # "分析我" 的变体
            do_analyze(chat_id, sender_open_id, target_open_id=sender_open_id)
        elif '帮助' in text or 'help' in text.lower():
            send_help(chat_id)
        else:
            # 默认：如果是私聊就分析，群聊就提示
            chat_type = message.get('chat_type', '')
            if chat_type == 'p2p':
                do_analyze(chat_id, sender_open_id, target_open_id=sender_open_id)
            else:
                feishu.send_text(chat_id, '发送「分析我」来获取你的人格基因分析报告 🧬')

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)


def handle_message_v1(event: dict):
    """处理 v1 消息事件 (兼容旧版)"""
    try:
        open_id = event.get('open_id', '')
        chat_id = event.get('open_chat_id', '') or event.get('chat_id', '')
        text = event.get('text_without_at_bot', '') or event.get('text', '')

        if '分析我' in text or '分析' in text:
            do_analyze(chat_id, open_id, target_open_id=open_id)
        elif '帮助' in text:
            send_help(chat_id)
    except Exception as e:
        logger.error(f"Error handling v1 message: {e}", exc_info=True)


def do_analyze(chat_id: str, requester_id: str, target_open_id: str):
    """执行人格分析"""
    try:
        # 1. 发送「正在分析」提示
        feishu.send_text(chat_id, '🧬 正在解析你的人格基因，请稍等...\n（正在读取最近的聊天记录并分析）')

        # 2. 拉取目标用户在该会话中的消息
        messages = feishu.fetch_user_messages(chat_id, target_open_id, limit=200)

        if not messages or len(messages) < 5:
            feishu.send_text(chat_id, '⚠️ 聊天记录太少（至少需要5条消息），多聊几句再来分析吧！')
            return

        logger.info(f"Fetched {len(messages)} messages for analysis")

        # 3. 获取用户信息
        user_info = feishu.get_user_info(target_open_id)
        user_name = user_info.get('name', '未知用户') if user_info else '未知用户'

        # 4. 调用 Claude 分析
        result = analyzer.analyze(messages, user_name=user_name)

        if not result:
            feishu.send_text(chat_id, '❌ 分析失败，请稍后重试')
            return

        logger.info(f"Analysis result for {user_name}: MBTI={result.get('mbti', {}).get('type')}, Gene={result.get('gene', {}).get('name')}")

        # 5. 构建并发送结果卡片
        card = card_builder.build_result_card(result, user_name, len(messages))
        feishu.send_card(chat_id, card)

    except Exception as e:
        logger.error(f"Error in do_analyze: {e}", exc_info=True)
        feishu.send_text(chat_id, f'❌ 分析出错: {str(e)[:100]}')


def send_help(chat_id: str):
    """发送帮助信息"""
    card = card_builder.build_help_card()
    feishu.send_card(chat_id, card)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'feishu-persona-bot'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    logger.info(f"Starting Feishu Persona Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
