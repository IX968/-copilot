"""
模型管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ...ai_framework.engine_manager import get_engine_manager
from ...ai_framework.model_registry import get_model_registry

router = APIRouter()


class LoadModelRequest(BaseModel):
    """加载模型请求"""
    model_name: str
    engine_type: Optional[str] = "transformer"


class ModelInfo(BaseModel):
    """模型信息"""
    name: str
    path: str
    size_gb: float
    model_type: str
    is_loaded: bool


@router.get("")
async def list_models() -> List[Dict[str, Any]]:
    """获取所有可用模型列表"""
    registry = get_model_registry()
    models = registry.scan_models()
    return registry.list_models(include_metadata=False)


@router.get("/loaded")
async def get_loaded_model():
    """获取当前已加载的模型"""
    registry = get_model_registry()
    model = registry.get_loaded_model()

    if model is None:
        return {"loaded": False, "model": None}

    return {
        "loaded": True,
        "model": {
            "name": model.name,
            "path": model.path,
            "size_gb": model.size_gb,
            "type": model.model_type,
        }
    }


@router.post("/load")
async def load_model(request: LoadModelRequest):
    """
    加载指定模型

    Args:
        request: 加载请求，包含模型名称和引擎类型
    """
    registry = get_model_registry()
    model_info = registry.get_model(request.model_name)

    if model_info is None:
        raise HTTPException(status_code=404, detail=f"模型未找到：{request.model_name}")

    engine_manager = get_engine_manager()

    # 只要进入加载流程，原模型必然会被抛弃，所以这里统一重置所有持久化的加载状态
    for model in registry.list_models():
        if model.get('is_loaded'):
            registry.set_loaded(model['name'], False)

    # 卸载当前模型
    if engine_manager.is_ready:
        engine_manager.unload_engine()

    # 加载新模型
    success = engine_manager.create_engine(request.engine_type, model_info.path)
    if not success:
        raise HTTPException(status_code=500, detail="引擎创建失败")

    success = engine_manager.load_engine()
    if not success:
        raise HTTPException(status_code=500, detail="模型加载失败")

    # 更新注册表
    registry.set_loaded(request.model_name, True)

    return {
        "success": True,
        "message": f"模型已加载：{request.model_name}",
        "model": model_info,
    }


@router.post("/unload")
async def unload_model():
    """卸载当前模型"""
    engine_manager = get_engine_manager()
    registry = get_model_registry()

    # 允许强制清理注册表中的幽灵加载状态
    current_model = engine_manager.current_model

    if engine_manager.is_ready:
        engine_manager.unload_engine()

    # 重置注册表中所有加载状态
    for model in registry.list_models():
        if model['is_loaded']:
            registry.set_loaded(model['name'], False)

    if not engine_manager.is_ready and not current_model:
        return {"success": True, "message": "已清理模型状态，但内存中没有运行的模型"}

    return {
        "success": True,
        "message": f"模型已卸载：{current_model or '未知'}",
    }


@router.delete("/{model_name}")
async def remove_model(model_name: str):
    """
    从注册表移除模型（不删除文件）

    Args:
        model_name: 模型名称
    """
    registry = get_model_registry()

    if model_name not in [m['name'] for m in registry.list_models()]:
        raise HTTPException(status_code=404, detail=f"模型未找到：{model_name}")

    # 如果是已加载模型，先卸载
    loaded_model = registry.get_loaded_model()
    if loaded_model and loaded_model.name == model_name:
        engine_manager = get_engine_manager()
        engine_manager.unload_engine()

    registry.remove_model(model_name)

    return {
        "success": True,
        "message": f"模型已从注册表移除：{model_name}",
    }


@router.post("/scan")
async def scan_models():
    """重新扫描模型目录"""
    registry = get_model_registry()
    models = registry.scan_models()

    return {
        "success": True,
        "count": len(models),
        "models": registry.list_models(),
    }
