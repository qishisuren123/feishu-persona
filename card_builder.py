"""
飞书互动卡片构建器
将 NMTI 分析结果转换为飞书消息卡片
"""


class CardBuilder:

    # NMTI 牛马类型描述
    NMTI_NAMES = {
        'INTJ': '闷头耕地型牛马', 'INTP': '带脑子的牛马', 'ENTJ': '牛马头子', 'ENTP': '抬杠型牛马',
        'INFJ': '有理想的牛马', 'INFP': '文艺牛马', 'ENFJ': '操心命牛马', 'ENFP': '快乐牛马',
        'ISTJ': '标准螺丝钉牛马', 'ISFJ': '任劳任怨牛马', 'ESTJ': '牛马监工', 'ESFJ': '团建牛马',
        'ISTP': '沉默手艺牛马', 'ISFP': '佛系牛马', 'ESTP': '敢死队牛马', 'ESFP': '快乐摸鱼牛马',
    }

    # 维度中文名
    DIM_NAMES = {
        'S_score': '🎯 谋略值', 'E_score': '💚 共情值', 'R_score': '🔥 冒险值',
        'X_score': '🗣️ 社交值', 'C_score': '👑 控制值', 'P_score': '🎭 表达值',
        'M_score': '⚖️ 底线值', 'I_score': '🦅 独立值',
    }

    def build_result_card(self, result: dict, user_name: str, msg_count: int) -> dict:
        """构建分析结果卡片"""
        nmti = result.get('nmti', result.get('mbti', {}))
        gene = result.get('gene', {})
        dims = result.get('dimensions', {})
        highlights = result.get('highlights', [])
        advice = result.get('advice', '')

        nmti_type = nmti.get('type', '????')
        nmti_name = self.NMTI_NAMES.get(nmti_type, '未知牛马')

        # 构建维度条形图文本
        dim_bars = []
        for key, label in self.DIM_NAMES.items():
            score = dims.get(key, 50)
            bar = self._make_bar(score)
            dim_bars.append(f'{label}  {bar}  **{score}**')

        dim_text = '\n'.join(dim_bars)

        # NMTI 维度详情
        nmti_dims = nmti.get('dimensions', {})
        nmti_details = []
        for dim_key in ['EI', 'SN', 'TF', 'JP']:
            d = nmti_dims.get(dim_key, {})
            r = d.get('result', '?')
            s = d.get('score', 50)
            reason = d.get('reason', '')
            nmti_details.append(f'**{dim_key}** → **{r}** ({s}%)  {reason}')
        nmti_detail_text = '\n'.join(nmti_details)

        # 亮点
        highlight_text = '\n'.join([f'• {h}' for h in highlights]) if highlights else '• 数据不足，暂无亮点'

        # 构建飞书卡片
        card = {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': f'🐂 {user_name} 的 NMTI 牛马报告'},
                'template': 'purple',
            },
            'elements': [
                # 牛马品种
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 🧬 牛马品种：{gene.get("name", "未知")}\n*{gene.get("subtitle", "")}*',
                    },
                },
                # 描述
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': gene.get('description', ''),
                    },
                },
                {'tag': 'hr'},
                # NMTI
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 📊 NMTI：{nmti_type}（{nmti_name}）\n{nmti.get("summary", "")}',
                    },
                },
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': nmti_detail_text,
                    },
                },
                {'tag': 'hr'},
                # 8维度
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 📈 牛马基因8维度\n{dim_text}',
                    },
                },
                {'tag': 'hr'},
                # 亮点
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'## 🔍 你的牛马特征\n{highlight_text}',
                    },
                },
                # 忠告
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': f'💡 **牛马忠告：** {advice}' if advice else '',
                    },
                },
                {'tag': 'hr'},
                # 底部
                {
                    'tag': 'note',
                    'elements': [
                        {
                            'tag': 'lark_md',
                            'content': f'基于 {msg_count} 条消息分析 · 测出来是牛马也别太难过 · Powered by [evomap](https://evomap.ai)',
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
                'title': {'tag': 'plain_text', 'content': '🐂 NMTI 牛马人格分析'},
                'template': 'purple',
            },
            'elements': [
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': (
                            '我可以通过分析你的聊天记录，测出你是哪种**牛马** 🐂\n\n'
                            '## 使用方式\n'
                            '**群聊中：** @我 并发送「分析我」\n'
                            '**私聊中：** 直接发送「分析我」\n\n'
                            '## NMTI 分析内容\n'
                            '• **NMTI 16型牛马** — 你是闷头耕地型还是快乐摸鱼型？\n'
                            '• **牛马基因8维度** — 谋略/共情/冒险/社交/控制/表达/底线/独立\n'
                            '• **牛马品种鉴定** — 你是职场狐狸还是带薪如厕哲学家？\n\n'
                            '## 注意\n'
                            '• 至少需要5条历史消息才能鉴定\n'
                            '• 消息越多鉴定越准（建议50条以上）\n'
                            '• 仅供娱乐，测出来是牛马也别太难过'
                        ),
                    },
                },
                {'tag': 'hr'},
                {
                    'tag': 'note',
                    'elements': [
                        {
                            'tag': 'lark_md',
                            'content': 'NMTI 牛马测序计划 · Powered by [evomap](https://evomap.ai)',
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
