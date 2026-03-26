"""
引擎切换 API 路由
提供在线切换推理引擎的接口（无需重启服务）
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SwitchEngineRequest(BaseModel):
    """引擎切换请求"""
    engine_type: str                     # transformer | exllama | api
    model_path: Optional[str] = None     # transformer / exllama 用，覆盖 config 中的路径
    api_base_url: Optional[str] = None   # api 引擎专用
    api_key: Optional[str] = None        # api 引擎专用
    api_model_id: Optional[str] = None   # api 引擎专用


@router.post("/engines/switch")
async def switch_engine(req: SwitchEngineRequest):
    """
    在线切换引擎并立即生效

    流程：
    1. 更新内存配置
    2. 持久化到 config.yaml
    3. 卸载当前引擎，加载新引擎
    """
    from app.config import config
    from backend.ai_framework.engine_manager import get_engine_manager

    # 更新配置（支持嵌套 key）
    config.set('engine', 'type', value=req.engine_type)
    if req.model_path:
        config.set('engine', 'model_path', value=req.model_path)
    if req.api_base_url:
        config.set('engine', 'api', 'base_url', value=req.api_base_url)
    if req.api_key is not None:
        config.set('engine', 'api', 'api_key', value=req.api_key)
    if req.api_model_id:
        config.set('engine', 'api', 'model_id', value=req.api_model_id)
    config.save()

    manager = get_engine_manager()

    # 提前检测依赖，返回可读的错误原因
    if req.engine_type == "exllama":
        try:
            import exllamav3  # noqa: F401
        except ImportError:
            return {
                "success": False,
                "engine_type": manager.current_engine_type,
                "message": "ExLlamaV3 未安装，请在 pytorch_python11 conda 环境中安装预编译 wheel",
            }
    elif req.engine_type == "api":
        try:
            import openai  # noqa: F401
        except ImportError:
            return {
                "success": False,
                "engine_type": manager.current_engine_type,
                "message": "openai 库未安装，请运行: pip install openai",
            }
    model_path = req.model_path or config.get('engine', 'model_path', default='')
    success = manager.switch_model(req.engine_type, model_path)

    # 如果引擎创建成功但 load_model 失败（如模型路径不存在），给出更具体的提示
    if not success and req.engine_type in ("transformer", "exllama") and not model_path:
        message = "引擎切换失败：未配置模型路径，请在模型管理页面先加载一个模型"
    elif not success:
        message = f"引擎切换失败（{req.engine_type}），请确认模型路径正确且文件存在"
    else:
        message = f"已切换到 {req.engine_type} 引擎"

    return {
        "success": success,
        "engine_type": manager.current_engine_type,
        "message": message,
    }


@router.get("/engines/available")
async def get_available_engines():
    """
    检测当前环境中可用的引擎

    根据库是否安装返回每个引擎的可用状态，
    前端可据此对不可用引擎显示提示。
    """
    result = [
        {
            "id": "transformer",
            "name": "Transformer (HuggingFace)",
            "available": True,
            "note": "CPU/GPU，safetensors 格式",
        }
    ]

    try:
        import exllamav3  # noqa: F401
        result.append({
            "id": "exllama",
            "name": "ExLlamaV3",
            "available": True,
            "note": "EXL3/EXL2/GGUF 量化格式，高性能 GPU 推理",
        })
    except ImportError:
        result.append({
            "id": "exllama",
            "name": "ExLlamaV3",
            "available": False,
            "note": "未安装（需 pytorch_python11 conda 环境）",
        })

    try:
        import openai  # noqa: F401
        result.append({
            "id": "api",
            "name": "云端 API",
            "available": True,
            "note": "OpenAI 兼容接口（DeepSeek/Qwen/智谱等）",
        })
    except ImportError:
        result.append({
            "id": "api",
            "name": "云端 API",
            "available": False,
            "note": "需安装: pip install openai",
        })

    return result
