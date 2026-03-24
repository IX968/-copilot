"""
AI 推理引擎抽象基类
所有引擎实现必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass


@dataclass
class GenerationRequest:
    """生成请求数据类"""
    context: str                          # 上下文文本
    max_tokens: int = 64                  # 最大生成 token 数
    temperature: float = 0.7              # 温度
    top_k: int = 40                       # Top-K
    top_p: float = 0.9                    # Top-P
    repetition_penalty: float = 1.1       # 重复惩罚
    stop_sequences: Optional[List[str]] = None  # 停止序列


@dataclass
class GenerationResult:
    """生成结果数据类"""
    text: str                             # 生成的文本
    tokens_generated: int = 0             # 生成的 token 数
    inference_time: float = 0.0           # 推理时间（秒）
    tokens_per_second: float = 0.0        # 生成速度
    model_id: str = ""                    # 模型 ID
    error: Optional[str] = None           # 错误信息

    @property
    def success(self) -> bool:
        """是否成功生成"""
        return self.error is None


class BaseEngine(ABC):
    """
    AI 推理引擎抽象基类

    所有引擎实现（Transformer/ExLlamaV2/API）必须继承此类
    实现所有抽象方法
    """

    def __init__(self, model_path: str):
        """
        初始化引擎

        Args:
            model_path: 模型路径或模型 ID
        """
        self.model_path = model_path
        self._is_ready = False

    @abstractmethod
    def load_model(self) -> bool:
        """
        加载模型

        Returns:
            bool: 加载是否成功
        """
        pass

    @abstractmethod
    def unload_model(self):
        """
        卸载模型，释放资源
        """
        pass

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        生成文本补全（一次性返回）

        Args:
            request: 生成请求

        Returns:
            GenerationResult: 生成结果
        """
        pass

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        """
        流式生成文本补全（逐 token 返回）

        子类可覆盖此方法实现真正的流式输出。
        默认实现：调用 generate() 后一次性 yield 全部文本（降级）。

        Args:
            request: 生成请求

        Yields:
            str: 每次生成的文本片段
        """
        result = self.generate(request)
        if result.success and result.text:
            yield result.text

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """引擎是否就绪"""
        pass

    @property
    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            dict: 包含模型名称、类型、参数量等信息
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            dict: 健康状态信息
        """
        return {
            "ready": self.is_ready,
            "model_path": self.model_path,
            "model_info": self.model_info if self.is_ready else None
        }

    def validate_context(self, context: str, max_length: int = 8000) -> str:
        """
        验证并截断上下文

        Args:
            context: 原始上下文
            max_length: 最大长度

        Returns:
            str: 处理后的上下文
        """
        if not context:
            return ""

        if len(context) > max_length:
            # 保留末尾部分
            return context[-max_length:]

        return context

    def __enter__(self):
        """上下文管理器入口"""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.unload_model()
