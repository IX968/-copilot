"""
ExLlamaV3 引擎 — 高性能量化模型推理
需要安装 exllamav3 预编译 wheel：
    pip install https://github.com/turboderp-org/exllamav3/releases/download/v0.0.26/exllamav3-0.0.26+cu128.torch2.10.0-cp311-cp311-win_amd64.whl --no-deps
    pip install kbnf formatron marisa-trie
"""
import time
from typing import Dict, Any, Iterator

from .base import BaseEngine, GenerationRequest, GenerationResult


class ExLlamaV2Engine(BaseEngine):
    """
    ExLlamaV3 推理引擎（向后兼容名称保持 ExLlamaV2Engine）

    支持 EXL3/EXL2/GGUF 量化格式，利用 RTX GPU 高速推理。
    model_path 需指向含模型权重的目录。
    """

    MAX_CACHE_TOKENS = 4096  # cache 总容量

    def __init__(self, model_path: str):
        super().__init__(model_path)
        self._model = None
        self._cache = None
        self._tokenizer = None
        self._generator = None
        self._config = None

    def load_model(self) -> bool:
        try:
            from exllamav3 import Config, Model, Tokenizer, Cache
            from exllamav3 import Generator, Job, ComboSampler
        except ImportError:
            print("[ExLlamaV3] 库未安装，请运行:")
            print("  pip install https://github.com/turboderp-org/exllamav3/releases/download/v0.0.26/exllamav3-0.0.26+cu128.torch2.10.0-cp311-cp311-win_amd64.whl --no-deps")
            print("  pip install kbnf formatron marisa-trie")
            return False

        try:
            self._config = Config.from_directory(self.model_path)
            self._model = Model.from_config(self._config)
            self._cache = Cache(self._model, max_num_tokens=4096)  # 必须在 load() 前创建，使 alloc() 能在加载时触发
            self._model.load()
            self._tokenizer = Tokenizer.from_config(self._config)
            self._generator = Generator(
                model=self._model,
                cache=self._cache,
                tokenizer=self._tokenizer,
            )
            self._is_ready = True
            print(f"[ExLlamaV3] 模型加载成功: {self.model_path}")
            return True
        except Exception as e:
            print(f"[ExLlamaV3] 模型加载失败: {e}")
            return False

    def unload_model(self):
        del self._generator, self._cache, self._model, self._tokenizer, self._config
        self._generator = None
        self._cache = None
        self._model = None
        self._tokenizer = None
        self._config = None
        self._is_ready = False

        import gc, torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[ExLlamaV3] 模型已卸载")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self._is_ready or self._generator is None:
            return GenerationResult(text="", error="ExLlamaV3 引擎未就绪")

        start = time.time()
        try:
            from exllamav3 import Job, ComboSampler

            context = self.validate_context(request.context)
            input_ids = self._tokenizer.encode(context)

            # 截断到 cache 容量，保留最近的上下文，留空间给输出
            max_input = self.MAX_CACHE_TOKENS - request.max_tokens
            if input_ids.shape[-1] > max_input:
                input_ids = input_ids[:, -max_input:]

            sampler = ComboSampler(
                temperature=request.temperature,
                top_k=request.top_k,
                top_p=request.top_p,
                rep_p=request.repetition_penalty,
            )

            stop_conditions = [self._tokenizer.eos_token_id]
            if request.stop_sequences:
                stop_conditions += request.stop_sequences

            job = Job(
                input_ids=input_ids,
                max_new_tokens=request.max_tokens,
                sampler=sampler,
                stop_conditions=stop_conditions,
            )
            self._generator.enqueue(job)

            output_text = ""
            while self._generator.num_remaining_jobs():
                for r in self._generator.iterate():
                    output_text += r.get("text", "")

            elapsed = time.time() - start
            tok_count = len(output_text.split())
            return GenerationResult(
                text=output_text,
                tokens_generated=tok_count,
                inference_time=elapsed,
                tokens_per_second=tok_count / elapsed if elapsed > 0 else 0,
                model_id=self.model_path,
            )
        except Exception as e:
            return GenerationResult(text="", error=str(e))

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        if not self._is_ready or self._generator is None:
            return

        try:
            from exllamav3 import Job, ComboSampler

            context = self.validate_context(request.context)
            input_ids = self._tokenizer.encode(context)

            # 截断到 cache 容量，保留最近的上下文，留空间给输出
            max_input = self.MAX_CACHE_TOKENS - request.max_tokens
            if input_ids.shape[-1] > max_input:
                input_ids = input_ids[:, -max_input:]

            sampler = ComboSampler(
                temperature=request.temperature,
                top_k=request.top_k,
                top_p=request.top_p,
                rep_p=request.repetition_penalty,
            )

            stop_conditions = [self._tokenizer.eos_token_id]
            if request.stop_sequences:
                stop_conditions += request.stop_sequences

            job = Job(
                input_ids=input_ids,
                max_new_tokens=request.max_tokens,
                sampler=sampler,
                stop_conditions=stop_conditions,
            )
            self._generator.enqueue(job)

            while self._generator.num_remaining_jobs():
                for r in self._generator.iterate():
                    chunk = r.get("text", "")
                    if chunk:
                        yield chunk
        except Exception as e:
            print(f"[ExLlamaV3] 流式生成失败: {e}")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def model_info(self) -> Dict[str, Any]:
        return {
            "model_path": self.model_path,
            "engine_type": "exllama",
            "engine_version": "exllamav3",
            "is_ready": self._is_ready,
        }
