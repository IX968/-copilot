"""
提示词管理器 — 支持多种补全模式的 prompt 模板切换
"""
from typing import Dict, Optional


# ── 内置提示词模板 ──────────────────────────────────────────────
PROMPT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "code": {
        "name": "代码补全",
        "prefix": "",                   # 代码模式：纯续写，不加前缀
        "suffix": "",
        "description": "直接续写代码，不添加任何说明",
    },
    "writing": {
        "name": "文档 / 论文写作",
        "prefix": (
            "[INST] 你是一名专业的学术写作与文档撰写助手。"
            "请根据上下文，以自然、连贯的语言继续撰写，"
            "保持与前文一致的风格、人称和术语。"
            "直接续写内容，不要输出标题、解释或元信息。 [/INST]\n"
        ),
        "suffix": "",
        "description": "学术论文、技术文档、报告等长文写作续写",
    },
}


class PromptManager:
    """
    管理当前激活的提示词模板，并在生成前包装上下文。
    """

    def __init__(self, default_mode: str = "code"):
        self._mode = default_mode if default_mode in PROMPT_TEMPLATES else "code"

    # ── 属性 ─────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    @property
    def mode_name(self) -> str:
        return PROMPT_TEMPLATES[self._mode]["name"]

    # ── 切换 ─────────────────────────────────────────────────
    def set_mode(self, mode: str) -> bool:
        if mode not in PROMPT_TEMPLATES:
            return False
        self._mode = mode
        print(f"[PromptManager] 切换到提示词模式：{mode} ({self.mode_name})")
        return True

    # ── 包装上下文 ───────────────────────────────────────────
    def wrap_context(self, raw_context: str) -> str:
        """在原始上下文前后拼接当前模板的 prefix / suffix"""
        tpl = PROMPT_TEMPLATES[self._mode]
        return f"{tpl['prefix']}{raw_context}{tpl['suffix']}"

    # ── 列出可用模式 ─────────────────────────────────────────
    @staticmethod
    def list_modes() -> list:
        return [
            {"key": k, "name": v["name"], "description": v["description"]}
            for k, v in PROMPT_TEMPLATES.items()
        ]


# ── 全局单例 ────────────────────────────────────────────────
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
