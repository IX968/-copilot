"""
提示词模式 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ...ai_framework.prompt_manager import get_prompt_manager

router = APIRouter()


class PromptModeRequest(BaseModel):
    mode: str  # "code" | "writing"


@router.get("/prompt/modes")
async def list_modes():
    """列出所有可用提示词模式"""
    pm = get_prompt_manager()
    return {
        "current": pm.mode,
        "current_name": pm.mode_name,
        "modes": pm.list_modes(),
    }


@router.post("/prompt/mode")
async def switch_mode(req: PromptModeRequest):
    """切换提示词模式"""
    pm = get_prompt_manager()
    if pm.set_mode(req.mode):
        return {
            "success": True,
            "mode": pm.mode,
            "name": pm.mode_name,
        }
    return {
        "success": False,
        "error": f"未知模式: {req.mode}",
        "available": [m["key"] for m in pm.list_modes()],
    }
