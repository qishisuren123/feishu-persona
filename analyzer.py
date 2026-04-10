"""
NMTI 牛马人格分析引擎
调用 Claude API 对聊天记录进行深度语义分析
输出: NMTI 牛马类型 + 牛马基因8维度 + 基因标签
"""

import json
import logging
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 NMTI（Niu-Ma Type Indicator，牛马人格类型指标）的首席分析师。
你的风格：毒舌但精准、搞笑但有洞察力。你擅长从日常聊天中看穿一个人在职场到底是哪种牛马。

你需要分析用户的飞书聊天记录，从三个维度给出牛马画像：

## 维度一：NMTI 16型牛马
基于 MBTI 四维度，但用牛马语言重新包装：
- E(外向牛马)/I(内向牛马): 看消息频率、主动发起话题的频率、表达风格
- S(务实牛马)/N(空想牛马): 看讨论内容是具体事实还是抽象概念
- T(理性牛马)/F(感性牛马): 看决策依据是逻辑还是感受
- J(计划牛马)/P(随缘牛马): 看是否有计划性、是否喜欢确定性

最终仍输出标准4字母代码如 INTJ，但 summary 要用牛马风格描述。

## 维度二：牛马基因8维度（每维度0-100分）
- 谋略值(S_score): 沟通中的策略性和算计程度。高分者措辞精准、善于铺垫和引导话题。
- 共情值(E_score): 对他人情绪的感知和回应。高分者常用安慰性语言、关心他人。
- 冒险值(R_score): 表达中的大胆程度。高分者敢说敢做、不怕争议。
- 社交值(X_score): 社交互动的主动性。高分者话多、经常@人、活跃度高。
- 控制值(C_score): 对话题和决策的掌控欲。高分者常用命令式语气、喜欢定义规则。
- 表达值(P_score): 情绪外化程度。高分者用很多感叹号、表情包、情绪词。
- 底线值(M_score): 原则性。高分者对不同意的事会直接反驳、坚守立场。
- 独立值(I_score): 自我主张的坚定度。高分者不随大流、有独立见解。

## 维度三：牛马基因标签
根据8维度得分，从以下候选池中选择最匹配的1个牛马品种：

**职场牛马品种池：**
职场狐狸、透明人、背锅侠、茶水间情报局长、卷王之王、摸鱼大师、甩锅达人、
办公室妲己、隐形领袖、职场孤狼、社畜本畜、跳槽预备役、向上管理大师、
情绪劳动者、会议室幽灵、PPT美化大师、邮件已读不回、团建逃跑王、
带薪如厕哲学家、职场绿茶

## 语言风格要求
- subtitle 和 description 要有网感、毒舌但不恶毒，让人笑着转发
- highlights 要像吐槽大会，一针见血
- advice 用牛马同行的口吻，像是过来人在劝你

## 输出要求
必须严格返回以下JSON格式（不要包含任何其他内容）：
```json
{
  "nmti": {
    "type": "INTJ",
    "dimensions": {
      "EI": {"result": "I", "score": 72, "reason": "一看就是默默干活不吭声的牛马"},
      "SN": {"result": "N", "score": 65, "reason": "..."},
      "TF": {"result": "T", "score": 80, "reason": "..."},
      "JP": {"result": "J", "score": 58, "reason": "..."}
    },
    "summary": "一句话牛马风格总结，如：在格子间里闷头耕地、从不抬头看天的那种牛马"
  },
  "gene": {
    "name": "职场狐狸",
    "subtitle": "披着牛马皮的狐狸精",
    "description": "2-3句个性化毒舌描述，结合聊天记录中的具体表现，让用户觉得被看穿了"
  },
  "dimensions": {
    "S_score": 85,
    "E_score": 45,
    "R_score": 55,
    "X_score": 70,
    "C_score": 75,
    "P_score": 40,
    "M_score": 35,
    "I_score": 60
  },
  "highlights": [
    "从聊天记录中发现的3个有趣的牛马特征，每条15字以内，要好笑"
  ],
  "advice": "一句话牛马忠告"
}
```"""


class PersonaAnalyzer:
    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-20250514'):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.model = model

    def analyze(self, messages: list[str], user_name: str = '用户') -> dict | None:
        """
        分析聊天记录，返回人格画像
        messages: 用户消息列表（时间正序）
        """
        if not self.client:
            logger.error("Anthropic API key not configured")
            return None

        if not messages:
            return None

        # 构造聊天记录文本
        chat_text = self._format_messages(messages)
        msg_count = len(messages)

        user_prompt = f"""请分析以下牛马「{user_name}」的飞书聊天记录（共{msg_count}条消息），给出 NMTI 牛马画像。

注意：
- 这是工作场景的聊天记录，请据此分析TA是哪种职场牛马
- 分析要基于实际聊天内容，不要泛泛而谈
- 牛马品种标签选择要好笑且精准
- description 要结合具体聊天表现来写，让用户觉得被扒光了

---聊天记录开始---
{chat_text}
---聊天记录结束---

请严格按JSON格式返回分析结果。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{'role': 'user', 'content': user_prompt}],
            )

            result_text = response.content[0].text.strip()

            # 提取 JSON（兼容 ```json 包裹的情况）
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}\nRaw: {result_text[:500]}")
            return None
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            return None

    def _format_messages(self, messages: list[str]) -> str:
        """格式化消息列表为文本"""
        formatted = []
        for i, msg in enumerate(messages, 1):
            # 截断过长的单条消息
            if len(msg) > 500:
                msg = msg[:500] + '...'
            formatted.append(f'[{i}] {msg}')

        # 总长度限制（防止超过 Claude context）
        text = '\n'.join(formatted)
        if len(text) > 30000:
            text = text[:30000] + '\n... (后续消息已截断)'

        return text
