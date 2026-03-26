"""
引擎管理器
负责引擎的创建、加载、卸载和健康检查
"""
import os
from pathlib import Path
from typing import Dict, Optional, Any, List

from ..engines.base import BaseEngine, GenerationRequest, GenerationResult


class EngineManager:
    """
    引擎管理器

    职责:
    - 根据配置创建对应的引擎实例
    - 管理引擎的生命周期（加载/卸载）
    - 提供统一的生成接口
    - 健康检查和性能监控
    """

    def __init__(self):
        """初始化引擎管理器"""
        self._engine: Optional[BaseEngine] = None
        self._engine_type: str = ""
        self._current_model: str = ""
        self._stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_inference_time": 0.0,
        }

    def create_engine(self, engine_type: str, model_path: str) -> bool:
        """
        根据类型创建引擎

        Args:
            engine_type: 引擎类型 (transformer | exllama | api)
            model_path: 模型路径

        Returns:
            bool: 创建是否成功
        """
        # 如果已有引擎，先卸载
        if self._engine is not None:
            self.unload_engine()

        self._engine_type = engine_type

        try:
            if engine_type == "transformer":
                from ..engines.transformer_engine import TransformerEngine
                self._engine = TransformerEngine(model_path)

            elif engine_type == "exllama":
                from ..engines.exllama_engine import ExLlamaV2Engine
                self._engine = ExLlamaV2Engine(model_path)

            elif engine_type == "api":
                from ..engines.api_engine import APIEngine
                self._engine = APIEngine(model_path)

            else:
                print(f"[EngineManager] 未知引擎类型：{engine_type}，使用 Transformer")
                from ..engines.transformer_engine import TransformerEngine
                self._engine = TransformerEngine(model_path)
                self._engine_type = "transformer"

            self._current_model = model_path
            print(f"[EngineManager] 引擎创建成功：{engine_type}, {model_path}")
            return True

        except Exception as e:
            print(f"[EngineManager] 引擎创建失败：{e}")
            self._engine = None
            return False

    def load_engine(self) -> bool:
        """
        加载当前引擎的模型

        Returns:
            bool: 加载是否成功
        """
        if self._engine is None:
            print("[EngineManager] 引擎未创建，无法加载")
            return False

        success = self._engine.load_model()
        if success:
            print("[EngineManager] 模型加载成功")
        else:
            print("[EngineManager] 模型加载失败")

        return success

    def unload_engine(self):
        """卸载当前引擎"""
        if self._engine is not None:
            self._engine.unload_model()
            self._engine = None
            print("[EngineManager] 引擎已卸载")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        生成文本补全

        Args:
            request: 生成请求

        Returns:
            GenerationResult: 生成结果
        """
        if self._engine is None:
            return GenerationResult(
                text="",
                error="引擎未初始化"
            )

        if not self._engine.is_ready:
            return GenerationResult(
                text="",
                error="引擎未就绪，请先加载模型"
            )

        # 记录请求
        self._stats["total_requests"] += 1

        # 执行生成
        result = self._engine.generate(request)

        # 更新统计
        if result.success:
            self._stats["successful_requests"] += 1
            self._stats["total_inference_time"] += result.inference_time
        else:
            self._stats["failed_requests"] += 1

        return result

    def generate_stream(self, request: GenerationRequest):
        """
        流式生成文本补全，委托给当前引擎的 generate_stream

        Args:
            request: 生成请求

        Yields:
            str: 每次生成的文本片段
        """
        if self._engine is None or not self._engine.is_ready:
            return

        yield from self._engine.generate_stream(request)

    def switch_model(self, engine_type: str, model_path: str) -> bool:
        """
        切换模型

        Args:
            engine_type: 新引擎类型
            model_path: 新模型路径

        Returns:
            bool: 切换是否成功
        """
        print(f"[EngineManager] 切换模型：{engine_type}, {model_path}")

        # 卸载当前模型
        self.unload_engine()

        # 创建新引擎
        if not self.create_engine(engine_type, model_path):
            return False

        # 加载新模型
        return self.load_engine()

    @property
    def is_ready(self) -> bool:
        """引擎是否就绪"""
        return self._engine is not None and self._engine.is_ready

    @property
    def current_model(self) -> str:
        """当前模型路径"""
        return self._current_model

    @property
    def current_engine_type(self) -> str:
        """当前引擎类型"""
        return self._engine_type

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()

        if stats["successful_requests"] > 0:
            stats["avg_inference_time"] = (
                stats["total_inference_time"] / stats["successful_requests"]
            )
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"]
            )
        else:
            stats["avg_inference_time"] = 0.0
            stats["success_rate"] = 0.0

        return stats

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if self._engine is None:
            return {
                "ready": False,
                "error": "引擎未初始化"
            }

        engine_health = self._engine.health_check()
        stats = self.get_stats()

        return {
            "ready": self.is_ready,
            "engine_type": self._engine_type,
            "model_path": self._current_model,
            "engine_info": engine_health.get("model_info", {}),
            "stats": stats,
        }

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_inference_time": 0.0,
        }


# 全局引擎管理器实例
_manager: Optional[EngineManager] = None


def get_engine_manager() -> EngineManager:
    """获取全局引擎管理器实例"""
    global _manager
    if _manager is None:
        _manager = EngineManager()
    return _manager
