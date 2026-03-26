"""
云端 API 引擎 — OpenAI 兼容接口
支持 DeepSeek、Qwen API、智谱、OpenAI 等任意兼容服务
"""
import time
from typing import Iterator, Dict, Any

from .base import BaseEngine, GenerationRequest, GenerationResult


class APIEngine(BaseEngine):
    """
    云端 API 推理引擎

    通过 OpenAI 兼容接口调用云端模型。
    API 配置从 config.yaml 的 engine.api 节读取。
    """

    def __init__(self, model_path: str = ""):
        super().__init__(model_path)
        self._client = None
        self._model_id = ""

    def load_model(self) -> bool:
        try:
            from openai import OpenAI
        except ImportError:
            print("[APIEngine] openai 库未安装，请运行: pip install openai")
            return False

        try:
            from app.config import config
            api_cfg = config.get('engine', 'api', default={}) or {}
            base_url = api_cfg.get('base_url', 'https://api.openai.com/v1')
            api_key = api_cfg.get('api_key', '')
            if not api_key:
                print("[APIEngine] 警告：API Key 未配置，请在控制台配置中心填入")
            self._model_id = api_cfg.get('model_id', 'gpt-3.5-turbo')
            self._client = OpenAI(api_key=api_key or "empty", base_url=base_url)
            self._is_ready = True
            print(f"[APIEngine] 就绪: {base_url}, model={self._model_id}")
            return True
        except Exception as e:
            print(f"[APIEngine] 初始化失败: {e}")
            return False

    def unload_model(self):
        self._client = None
        self._is_ready = False

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self._is_ready or self._client is None:
            return GenerationResult(text="", error="API 引擎未就绪")

        start = time.time()
        try:
            resp = self._client.chat.completions.create(
                model=self._model_id,
                messages=[
                    {"role": "system", "content": "你是代码/文本补全助手，直接续写用户给出的内容，不要解释。"},
                    {"role": "user", "content": request.context},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=False,
            )
            text = resp.choices[0].message.content or ""
            elapsed = time.time() - start
            tokens = resp.usage.completion_tokens if resp.usage else 0
            return GenerationResult(
                text=text,
                tokens_generated=tokens,
                inference_time=elapsed,
                tokens_per_second=tokens / elapsed if elapsed > 0 else 0,
                model_id=self._model_id,
            )
        except Exception as e:
            return GenerationResult(text="", error=str(e))

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        if not self._is_ready or self._client is None:
            return

        try:
            resp = self._client.chat.completions.create(
                model=self._model_id,
                messages=[
                    {"role": "system", "content": "你是代码/文本补全助手，直接续写用户给出的内容，不要解释。"},
                    {"role": "user", "content": request.context},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            print(f"[APIEngine] 流式生成失败: {e}")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def model_info(self) -> Dict[str, Any]:
        from app.config import config
        api_cfg = config.get('engine', 'api', default={}) or {}
        return {
            "model_path": api_cfg.get('base_url', ''),
            "model_id": self._model_id,
            "engine_type": "api",
            "is_ready": self._is_ready,
        }
