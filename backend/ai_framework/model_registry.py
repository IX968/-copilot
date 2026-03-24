"""
模型注册表
扫描和管理本地模型文件
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ModelInfo:
    """模型信息数据类"""
    name: str                      # 模型名称
    path: str                      # 模型路径
    size_gb: float = 0.0           # 大小（GB）
    model_type: str = "unknown"    # 模型类型
    is_loaded: bool = False        # 是否已加载
    metadata: Optional[Dict] = None  # 元数据


class ModelRegistry:
    """
    模型注册表

    职责:
    - 扫描 models/ 目录发现可用模型
    - 维护模型元数据
    - 提供模型加载状态追踪
    """

    def __init__(self, models_dir: str = "models"):
        """
        初始化模型注册表

        Args:
            models_dir: 模型目录路径
        """
        self.models_dir = Path(models_dir)
        self._models: Dict[str, ModelInfo] = {}
        self._registry_file = self.models_dir / ".model_registry.json"
        self._load_registry()

    def _load_registry(self):
        """从文件加载注册表"""
        if self._registry_file.exists():
            try:
                with open(self._registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        model_info = ModelInfo(**info)
                        # 重启时强制重置状态，因为显存中的模型已清空
                        model_info.is_loaded = False
                        self._models[name] = model_info
                print(f"[ModelRegistry] 已加载 {len(self._models)} 个模型")
            except Exception as e:
                print(f"[ModelRegistry] 加载注册表失败：{e}")
                self._models = {}

    def _save_registry(self):
        """保存注册表到文件"""
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            data = {
                name: asdict(info) for name, info in self._models.items()
            }
            with open(self._registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ModelRegistry] 保存注册表失败：{e}")

    def scan_models(self) -> List[ModelInfo]:
        """
        扫描模型目录

        Returns:
            List[ModelInfo]: 发现的模型列表
        """
        if not self.models_dir.exists():
            self.models_dir.mkdir(parents=True, exist_ok=True)
            return []

        models = []

        # 扫描目录
        for item in self.models_dir.iterdir():
            if not item.is_dir():
                continue

            # 跳过隐藏目录和特殊文件
            if item.name.startswith('.') or item.name == '__pycache__':
                continue

            # 检查是否为有效模型目录
            model_info = self._inspect_model_dir(item)
            if model_info:
                models.append(model_info)

                # 更新注册表
                if item.name not in self._models:
                    self._models[item.name] = model_info
                else:
                    # 保留加载状态
                    self._models[item.name].size_gb = model_info.size_gb
                    self._models[item.name].model_type = model_info.model_type

        self._save_registry()
        print(f"[ModelRegistry] 扫描完成，发现 {len(models)} 个模型")
        return models

    def _inspect_model_dir(self, path: Path) -> Optional[ModelInfo]:
        """
        检查目录是否为有效模型

        Args:
            path: 模型目录路径

        Returns:
            ModelInfo or None: 模型信息或 None
        """
        # 检查必需的模型文件
        model_files = [
            'config.json',           # 模型配置
        ]

        weight_patterns = [
            'pytorch_model.bin',
            'pytorch_model.safetensors',
            'model.safetensors',
            '*.safetensors',
        ]

        has_config = any((path / f).exists() for f in model_files)

        has_weights = False
        for pattern in weight_patterns:
            if pattern.startswith('*.'):
                # 通配符匹配
                matches = list(path.glob(pattern))
                if matches:
                    has_weights = True
                    break
            else:
                if (path / pattern).exists():
                    has_weights = True
                    break

        if not (has_config or has_weights):
            return None

        # 计算大小
        total_size = sum(
            f.stat().st_size
            for f in path.rglob('*')
            if f.is_file()
        )
        size_gb = total_size / (1024 ** 3)

        # 推断模型类型
        model_type = "unknown"
        if (path / 'pytorch_model.bin').exists():
            model_type = "pytorch"
        elif (path / 'model.safetensors').exists() or list(path.glob('*.safetensors')):
            model_type = "safetensors"
        elif (path / 'ggml-model.bin').exists() or list(path.glob('*.gguf')):
            model_type = "gguf"

        # 检查是否已加载
        is_loaded = self._models.get(path.name, ModelInfo("", "")).is_loaded

        return ModelInfo(
            name=path.name,
            path=str(path),
            size_gb=round(size_gb, 2),
            model_type=model_type,
            is_loaded=is_loaded,
        )

    def list_models(self, include_metadata: bool = False) -> List[Dict[str, Any]]:
        """
        列出所有模型

        Args:
            include_metadata: 是否包含完整元数据

        Returns:
            List[Dict]: 模型信息列表
        """
        models = []
        for info in self._models.values():
            data = asdict(info)
            if not include_metadata:
                data.pop('metadata', None)
            models.append(data)
        return models

    def get_model(self, name: str) -> Optional[ModelInfo]:
        """获取指定模型信息"""
        return self._models.get(name)

    def set_loaded(self, name: str, is_loaded: bool):
        """设置模型加载状态"""
        if name in self._models:
            self._models[name].is_loaded = is_loaded
            self._save_registry()

    def get_loaded_model(self) -> Optional[ModelInfo]:
        """获取当前已加载的模型"""
        for info in self._models.values():
            if info.is_loaded:
                return info
        return None

    def remove_model(self, name: str) -> bool:
        """
        从注册表移除模型（不删除文件）

        Args:
            name: 模型名称

        Returns:
            bool: 是否成功移除
        """
        if name in self._models:
            del self._models[name]
            self._save_registry()
            return True
        return False


# 全局注册表实例
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """获取全局模型注册表实例"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
