"""
文本生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ...ai_framework.engine_manager import get_engine_manager
from ...engines.base import GenerationRequest

router = APIRouter()


class GenerateRequest(BaseModel):
    """生成请求"""
    context: str                        # 上下文文本
    max_tokens: int = 64               # 最大生成 token 数
    temperature: float = 0.7           # 温度
    top_k: int = 40                    # Top-K
    top_p: float = 0.9                 # Top-P
    repetition_penalty: float = 1.1    # 重复惩罚


class GenerateResponse(BaseModel):
    """生成响应"""
    text: str                          # 生成的文本
    tokens_generated: int              # 生成的 token 数
    inference_time: float              # 推理时间（秒）
    tokens_per_second: float           # 生成速度
    success: bool                      # 是否成功


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    生成文本补全

    Args:
        request: 生成请求

    Returns:
        GenerateResponse: 生成结果
    """
    engine_manager = get_engine_manager()

    # 检查引擎状态
    if not engine_manager.is_ready:
        raise HTTPException(
            status_code=503,
            detail="引擎未就绪，请先加载模型"
        )

    # 构建生成请求
    gen_request = GenerationRequest(
        context=request.context,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_k=request.top_k,
        top_p=request.top_p,
        repetition_penalty=request.repetition_penalty,
    )

    # 执行生成
    result = engine_manager.generate(gen_request)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "生成失败"
        )

    return GenerateResponse(
        text=result.text,
        tokens_generated=result.tokens_generated,
        inference_time=result.inference_time,
        tokens_per_second=result.tokens_per_second,
        success=True,
    )


@router.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    """
    流式生成（Server-Sent Events）

    逐 token 推送，客户端实时收到每个文本片段
    """
    import json
    import asyncio
    from fastapi.responses import StreamingResponse

    engine_manager = get_engine_manager()

    if not engine_manager.is_ready:
        raise HTTPException(
            status_code=503,
            detail="引擎未就绪，请先加载模型"
        )

    gen_request = GenerationRequest(
        context=request.context,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_k=request.top_k,
        top_p=request.top_p,
        repetition_penalty=request.repetition_penalty,
    )

    async def event_generator():
        loop = asyncio.get_event_loop()
        gen = engine_manager.generate_stream(gen_request)

        def _next(g):
            """在线程池中获取下一个 token，避免阻塞事件循环"""
            try:
                return next(g), False
            except StopIteration:
                return None, True

        try:
            while True:
                chunk, done = await loop.run_in_executor(None, _next, gen)
                if done:
                    break
                if chunk:
                    data = json.dumps({"token": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
