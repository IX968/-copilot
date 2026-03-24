"""
上下文构建器
基于记忆历史增强当前上下文
"""
import time
from typing import List, Dict, Any, Optional

from .storage import MemoryStorage, Interaction


class ContextBuilder:
    """
    上下文构建器

    职责:
    - 从历史记忆中检索相关上下文
    - 构建增强的提示词
    - 提取思想/变量/环境结构
    """

    def __init__(self, storage: MemoryStorage = None):
        """
        初始化上下文构建器

        Args:
            storage: 记忆存储实例
        """
        self.storage = storage or MemoryStorage()
        self.max_context_length = 4000
        self.similarity_threshold = 0.6

    def build_enhanced_context(
        self,
        current_context: str,
        app_name: str = "",
        max_relevant: int = 5
    ) -> str:
        """
        构建增强的上下文

        Args:
            current_context: 当前上下文
            app_name: 当前应用名称
            max_relevant: 最多关联的历史记录数

        Returns:
            str: 增强后的上下文
        """
        if not current_context:
            return ""

        # 获取相关的历史上下文
        relevant_contexts = self._find_relevant_contexts(
            current_context,
            app_name,
            max_relevant
        )

        if not relevant_contexts:
            return current_context

        # 构建增强上下文
        enhanced = current_context

        # 添加历史上下文（简略版）
        history_summary = self._summarize_contexts(relevant_contexts)
        if history_summary:
            enhanced = f"{history_summary}\n\n--- 当前上下文 ---\n{current_context}"

        # 截断到最大长度
        if len(enhanced) > self.max_context_length:
            enhanced = enhanced[-self.max_context_length:]

        return enhanced

    def _find_relevant_contexts(
        self,
        current_context: str,
        app_name: str,
        max_relevant: int
    ) -> List[Interaction]:
        """
        查找相关的历史上下文

        简单实现：基于应用名称和最近记录
        TODO: 实现语义相似度搜索

        Args:
            current_context: 当前上下文
            app_name: 当前应用名称
            max_relevant: 最多返回数量

        Returns:
            List[Interaction]: 相关的交互记录
        """
        # 优先获取同应用的记录
        if app_name:
            contexts = self.storage.get_interactions(
                app_name=app_name,
                limit=max_relevant,
                accepted_only=True
            )
            if contexts:
                return contexts

        # 获取最近的接受记录
        return self.storage.get_interactions(
            limit=max_relevant,
            accepted_only=True
        )

    def _summarize_contexts(self, contexts: List[Interaction]) -> str:
        """
        总结历史上下文

        Args:
            contexts: 交互记录列表

        Returns:
            str: 总结文本
        """
        if not contexts:
            return ""

        lines = ["--- 历史参考 ---"]

        for ctx in contexts[:3]:  # 最多显示 3 条
            # 简化显示
            input_short = ctx.input_context[:50].replace('\n', '\\n')
            output_short = ctx.output_completion[:50].replace('\n', '\\n')
            lines.append(f"输入：{input_short}... → 输出：{output_short}...")

        return '\n'.join(lines)

    def extract_structure(
        self,
        context: str,
        app_name: str = ""
    ) -> Dict[str, Any]:
        """
        从上下文提取结构（思想/变量/环境）

        简单启发式实现
        TODO: 使用 AI 模型进行提取

        Args:
            context: 上下文文本
            app_name: 应用名称

        Returns:
            Dict: 提取的结构
        """
        structure = {
            "thoughts": [],      # 思想/模式
            "variables": [],     # 变量名
            "environment": {     # 环境信息
                "app": app_name,
                "timestamp": time.time(),
                "context_length": len(context),
            }
        }

        # 简单启发式：提取可能的变量名（Python 风格）
        import re
        var_pattern = r'\b([a-z_][a-z0-9_]*)\s*='
        matches = re.findall(var_pattern, context)
        structure["variables"] = list(set(matches))[:10]  # 最多 10 个

        # 检测代码模式
        if 'def ' in context:
            structure["thoughts"].append("Python 函数定义")
        if 'class ' in context:
            structure["thoughts"].append("Python 类定义")
        if 'import ' in context:
            structure["thoughts"].append("Python 导入语句")
        if 'function' in context or '=>' in context:
            structure["thoughts"].append("JavaScript/TypeScript 代码")

        return structure

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.storage.get_stats()


# 全局构建器实例
_builder: Optional[ContextBuilder] = None


def get_context_builder() -> ContextBuilder:
    """获取全局上下文构建器实例"""
    global _builder
    if _builder is None:
        _builder = ContextBuilder()
    return _builder
