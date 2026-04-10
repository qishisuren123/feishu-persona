"""
飞书 API 客户端
负责: 鉴权、消息收发、历史消息拉取、用户信息获取
"""

import time
import json
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = 'https://open.feishu.cn/open-apis'


class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_token = None
        self._token_expires_at = 0

    # ==================== 鉴权 ====================

    @property
    def tenant_token(self) -> str:
        """获取 tenant_access_token，自动续期"""
        if self._tenant_token and time.time() < self._token_expires_at - 60:
            return self._tenant_token

        resp = requests.post(
            f'{BASE_URL}/auth/v3/tenant_access_token/internal',
            json={'app_id': self.app_id, 'app_secret': self.app_secret},
            timeout=10,
        )
        data = resp.json()

        if data.get('code') != 0:
            logger.error(f"Failed to get tenant token: {data}")
            raise RuntimeError(f"Feishu auth failed: {data.get('msg')}")

        self._tenant_token = data['tenant_access_token']
        self._token_expires_at = time.time() + data.get('expire', 7200)
        logger.info("Refreshed tenant_access_token")
        return self._tenant_token

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.tenant_token}',
            'Content-Type': 'application/json; charset=utf-8',
        }

    # ==================== 发送消息 ====================

    def send_text(self, chat_id: str, text: str):
        """发送文本消息"""
        resp = requests.post(
            f'{BASE_URL}/im/v1/messages?receive_id_type=chat_id',
            headers=self._headers(),
            json={
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': text}),
            },
            timeout=10,
        )
        data = resp.json()
        if data.get('code') != 0:
            logger.error(f"Send text failed: {data}")
        return data

    def send_card(self, chat_id: str, card: dict):
        """发送互动卡片"""
        resp = requests.post(
            f'{BASE_URL}/im/v1/messages?receive_id_type=chat_id',
            headers=self._headers(),
            json={
                'receive_id': chat_id,
                'msg_type': 'interactive',
                'content': json.dumps(card),
            },
            timeout=10,
        )
        data = resp.json()
        if data.get('code') != 0:
            logger.error(f"Send card failed: {data}")
        return data

    # ==================== 消息历史 ====================

    def fetch_user_messages(self, chat_id: str, user_open_id: str, limit: int = 200) -> list:
        """
        拉取指定用户在某会话中的历史消息
        返回纯文本消息列表 (最新的在后面)
        """
        all_messages = []
        page_token = None
        fetched = 0

        while fetched < limit * 3:  # 多拉一些，因为要过滤非目标用户的
            params = {
                'container_id_type': 'chat',
                'container_id': chat_id,
                'page_size': min(50, limit * 3 - fetched),
                'sort_type': 'ByCreateTimeDesc',  # 最新在前
            }
            if page_token:
                params['page_token'] = page_token

            resp = requests.get(
                f'{BASE_URL}/im/v1/messages',
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            data = resp.json()

            if data.get('code') != 0:
                logger.error(f"Fetch messages failed: {data}")
                break

            items = data.get('data', {}).get('items', [])
            if not items:
                break

            for item in items:
                sender_id = item.get('sender', {}).get('id', '')
                msg_type = item.get('msg_type', '')

                # 只要目标用户的文本消息
                if sender_id == user_open_id and msg_type == 'text':
                    try:
                        body = json.loads(item.get('body', {}).get('content', '{}'))
                        text = body.get('text', '').strip()
                        if text:
                            all_messages.append(text)
                    except (json.JSONDecodeError, AttributeError):
                        pass

                if len(all_messages) >= limit:
                    break

            fetched += len(items)
            page_token = data.get('data', {}).get('page_token')
            has_more = data.get('data', {}).get('has_more', False)

            if not has_more or len(all_messages) >= limit:
                break

        # 翻转为时间正序
        all_messages.reverse()
        return all_messages[:limit]

    # ==================== 用户信息 ====================

    def get_user_info(self, open_id: str) -> dict:
        """获取用户基本信息"""
        try:
            resp = requests.get(
                f'{BASE_URL}/contact/v3/users/{open_id}',
                headers=self._headers(),
                params={'user_id_type': 'open_id'},
                timeout=10,
            )
            data = resp.json()
            if data.get('code') == 0:
                return data.get('data', {}).get('user', {})
            logger.warning(f"Get user info failed: {data}")
        except Exception as e:
            logger.warning(f"Get user info error: {e}")
        return {}
