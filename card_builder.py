"""
飞书互动卡片构建器
将分析结果转换为精美的飞书消息卡片
"""


class CardBuilder:

    # MBTI 类型描述
    MBTI_NAMES = {
        'INTJ': '策略家', 'INTP': '逻辑学家', 'ENTJ': '指挥官', 'ENTP': '辩论家',
        'INFJ': '提倡者', 'INFP': '调停者', 'ENFJ': '主人公', 'ENFP': '竞选者',
        'ISTJ': '物流师', 'ISFJ': '守卫者', 'ESTJ': '总经理', 'ESFJ': '执政官',
        'ISTP': '鉴赏家', 'ISFP': '探险家', 'ESTP': '企业家', 'ESFP': '表演者',
    }

    # 维度中文名
    DIM_NAMES = {
        'S_score': '🎯 谋略值', 'E_score': '💚 共情值', 'R_score': '🔥 冒险值',
        'X_score': '🗣️ 社交值', 'C_score': '👑 控制值', 'P_score': '🎭 表达值',
        'M_score': '⚖️ 底线值', 'I_score': '🦅 独立值',
    }

    def build_result_card(self, result: dict, user_name: str, msg_count: int) -> dict:
        """构建分析结果卡片"""
        mbti = result.get('mbti', {})
        gene = result.get('gene', {})
        dims = result.get('dimensions', {})
        highlights = result.get('highlights', [])
        advice = result.get('advice', '')

        mbti_type = mbti.get('type', '????')
        mbti_name = self.MBTI_NAMES.get(mbti_type, '未知类型')

        # 构建维度条形图文本
        dim_bars = []
        for key, label in self.DIM_NAMES.items():
            score = dims.get(key, 50)
            bar = self._make_bar(score)
            dim_bars.append(f'{label}  {bar}  **{score}**')

        dim_text = '\n'.join(dim_bars)

        # MBTI 维度详情
        mbti_dims = mbti.get('dimensions', {})
        mbti_details = []
        for dim_key in ['EI', 'SN', 'TF', 'JP']:
            d = mbti_dims.get(dim_key, {})
            r = d.get('result', '?')
            s = d.get('score', 50)
            reason = d.get('reason', '')
            mbti_details.append(f'**{dim_key}** → **{r}** ({s}%)  {reason}')
        mbti_detail_text = '\n'.join(mbti_details)

        # 亮点
        highlight_text = '\n'.join([f'• {h}' for h in highlights]) if highlights else '• 数据不足，暂无亮点'

        # 构建飞书卡片
        card = {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': f'🧬 {user_name} 的人格基因报告'},
                'template': 'purple',
            },
            'elements': [
                # 基因名称
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 🧬 人格基因：{gene.get("name", "未知")}\n*{gene.get("subtitle", "")}*',
                    },
                },
                # 基因描述
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': gene.get('description', ''),
                    },
                },
                {'tag': 'hr'},
                # MBTI
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 📊 MBTI：{mbti_type} ({mbti_name})\n{mbti.get("summary", "")}',
                    },
                },
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': mbti_detail_text,
                    },
                },
                {'tag': 'hr'},
                # 8维度
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 📈 人格基因8维度\n{dim_text}',
                    },
                },
                {'tag': 'hr'},
                # 亮点发现
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 🔍 聊天中的人格线索\n{highlight_text}',
                    },
                },
                # 建议
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'💡 **一句话建议：** {advice}' if advice else '',
                    },
                },
                {'tag': 'hr'},
                # 底部
                {
                    'tag': 'note',
                    'elements': [
                        {
                            'tag': 'lark_md',
                            'content': f'基于 {msg_count} 条消息分析 · 仅供娱乐参考 · Powered by [evomap](https://evomap.ai)',
                        }
                    ],
                },
            ],
        }

        return card

    def build_help_card(self) -> dict:
        """构建帮助卡片"""
        return {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': '🧬 人格基因分析机器人'},
                'template': 'purple',
            },
            'elements': [
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': (
                            '我可以通过分析你的聊天记录，解码你隐藏的**人格基因** 🧬\n\n'
                            '## 使用方式\n'
                            '**群聊中：** @我 并发送「分析我」\n'
                            '**私聊中：** 直接发送「分析我」\n\n'
                            '## 分析内容\n'
                            '• **MBTI 16型人格** — 你是哪种类型？\n'
                            '• **人格基因8维度** — 谋略/共情/冒险/社交/控制/表达/底线/独立\n'
                            '• **人格基因标签** — 你是职场狐狸还是摸鱼大师？\n\n'
                            '## 注意\n'
                            '• 至少需要5条历史消息才能分析\n'
                            '• 消息越多分析越准（建议50条以上）\n'
                            '• 本工具仅供娱乐，结果不构成心理学诊断'
                        ),
                    },
                },
                {'tag': 'hr'},
                {
                    'tag': 'note',
                    'elements': [
                        {
                            'tag': 'lark_md',
                            'content': '人格基因测序计划 · Powered by [evomap](https://evomap.ai)',
                        }
                    ],
                },
            ],
        }

    @staticmethod
    def _make_bar(score: int, length: int = 10) -> str:
        """生成文本进度条"""
        filled = round(score / 100 * length)
        empty = length - filled
        return '█' * filled + '░' * empty
