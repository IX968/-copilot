"""
记忆系统 API 路由
提供交互历史的查询、搜索、删除接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...memory.storage import get_memory_storage

router = APIRouter()


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    limit: int = 20


@router.get("")
async def list_interactions(
    limit: int = 50,
    offset: int = 0,
    app_name: Optional[str] = None,
    accepted_only: bool = False,
):
    """
    获取交互记录列表（分页）

    Args:
        limit: 每页数量（默认 50）
        offset: 偏移量
        app_name: 按应用名称过滤
        accepted_only: 只返回已接受的记录
    """
    storage = get_memory_storage()
    interactions = storage.get_interactions(
        limit=limit,
        offset=offset,
        app_name=app_name,
        accepted_only=accepted_only,
    )

    return [
        {
            "id": i.id,
            "timestamp": i.timestamp,
            "app_name": i.app_name,
            "input_context": i.input_context[:200],  # 截断，避免传输过大
            "output_completion": i.output_completion[:200],
            "accepted": i.accepted,
        }
        for i in interactions
    ]


@router.post("/search")
async def search_interactions(req: SearchRequest):
    """搜索交互记录"""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")

    storage = get_memory_storage()
    results = storage.search_interactions(req.query, limit=req.limit)

    return [
        {
            "id": i.id,
            "timestamp": i.timestamp,
            "app_name": i.app_name,
            "input_context": i.input_context[:200],
            "output_completion": i.output_completion[:200],
            "accepted": i.accepted,
        }
        for i in results
    ]


@router.get("/stats")
async def get_stats():
    """获取记忆系统统计信息"""
    storage = get_memory_storage()
    return storage.get_stats()


@router.delete("/{interaction_id}")
async def delete_interaction(interaction_id: int):
    """删除单条交互记录"""
    storage = get_memory_storage()
    deleted = storage.delete_interaction(interaction_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"记录未找到：{interaction_id}")

    return {"success": True, "message": f"记录已删除：{interaction_id}"}


@router.post("/clear")
async def clear_all():
    """清空所有交互记录"""
    storage = get_memory_storage()
    storage.clear_all()
    return {"success": True, "message": "所有记忆已清空"}
