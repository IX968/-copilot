"""
Transformer 推理引擎
基于 Hugging Face Transformers 库
"""
import time
import threading
import torch
from typing import Dict, Any, Optional, Iterator
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from ..engines.base import BaseEngine, GenerationRequest, GenerationResult


class TransformerEngine(BaseEngine):
    """
    Transformer 推理引擎

    使用 Hugging Face Transformers 加载和运行模型
    支持自动设备映射（CUDA/CPU）
    """

    def __init__(self, model_path: str):
        """
        初始化 Transformer 引擎

        Args:
            model_path: 模型路径或 HuggingFace 模型 ID
        """
        super().__init__(model_path)
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device: str = "cpu"

    def load_model(self) -> bool:
        """加载 Transformer 模型"""
        try:
            print(f"[Transformer] 正在加载模型：{self.model_path}")

            # 检测可用设备
            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"[Transformer] 使用 GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                print("[Transformer] 未检测到 GPU，使用 CPU")

            # 加载模型
            print("[Transformer] 加载模型权重...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
            )

            # 加载分词器
            print("[Transformer] 加载分词器...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
            )

            self._is_ready = True
            print(f"[Transformer] 模型加载完成，就绪状态：{self.is_ready}")
            return True

        except Exception as e:
            print(f"[Transformer] 模型加载失败：{e}")
            import traceback
            traceback.print_exc()
            self._is_ready = False
            return False

    def unload_model(self):
        """卸载模型，释放显存"""
        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        # 强制垃圾回收 + 清理 CUDA 缓存
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self._is_ready = False
        print("[Transformer] 模型已卸载")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        使用 Transformer 生成文本

        Args:
            request: 生成请求

        Returns:
            GenerationResult: 生成结果
        """
        if not self.is_ready:
            return GenerationResult(
                text="",
                error="引擎未就绪，请先加载模型"
            )

        # 验证并截断上下文
        context = self.validate_context(request.context, max_length=8000)
        if not context:
            return GenerationResult(
                text="",
                error="上下文为空"
            )

        start_time = time.time()

        try:
            # 分词
            inputs = self.tokenizer(
                context,
                return_tensors="pt",
                truncation=True,
                max_length=8000,
            ).to(self.model.device)

            input_len = inputs.input_ids.shape[1]

            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    do_sample=request.temperature > 0,
                    top_k=request.top_k,
                    top_p=request.top_p,
                    repetition_penalty=request.repetition_penalty,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # 解码新生成的部分
            new_tokens = outputs[0][input_len:]
            new_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

            # 计算统计信息
            inference_time = time.time() - start_time
            tokens_generated = len(new_tokens)
            tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0

            return GenerationResult(
                text=new_text,
                tokens_generated=tokens_generated,
                inference_time=inference_time,
                tokens_per_second=tokens_per_second,
                model_id=self.model_path,
            )

        except Exception as e:
            return GenerationResult(
                text="",
                error=f"生成失败：{str(e)}"
            )

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        """
        流式生成文本（逐 token yield）

        使用 TextIteratorStreamer 在子线程中运行 model.generate，
        主线程通过迭代器逐个获取生成的文本片段。

        Args:
            request: 生成请求

        Yields:
            str: 每次生成的文本片段
        """
        if not self.is_ready:
            return

        context = self.validate_context(request.context, max_length=8000)
        if not context:
            return

        try:
            inputs = self.tokenizer(
                context,
                return_tensors="pt",
                truncation=True,
                max_length=8000,
            ).to(self.model.device)

            # 创建流式迭代器，跳过 prompt 部分，过滤特殊 token
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            # 生成参数
            generate_kwargs = dict(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=request.temperature > 0,
                top_k=request.top_k,
                top_p=request.top_p,
                repetition_penalty=request.repetition_penalty,
                pad_token_id=self.tokenizer.eos_token_id,
                streamer=streamer,
            )

            # 在子线程中运行 model.generate（它是阻塞的）
            thread = threading.Thread(
                target=self._generate_in_thread,
                args=(generate_kwargs,),
            )
            thread.start()

            # 主线程逐个 yield 生成的文本片段
            for text_chunk in streamer:
                if text_chunk:
                    yield text_chunk

            thread.join()

        except Exception as e:
            print(f"[Transformer] 流式生成失败：{e}")

    def _generate_in_thread(self, generate_kwargs: dict):
        """在子线程中运行 model.generate（供 generate_stream 使用）"""
        try:
            with torch.no_grad():
                self.model.generate(**generate_kwargs)
        except Exception as e:
            print(f"[Transformer] 子线程生成失败：{e}")

    @property
    def is_ready(self) -> bool:
        """引擎是否就绪"""
        return self._is_ready and self.model is not None and self.tokenizer is not None

    @property
    def model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self.is_ready:
            return {"error": "模型未加载"}

        # 估算参数数量
        num_parameters = sum(p.numel() for p in self.model.parameters()) if self.model else 0

        return {
            "model_path": self.model_path,
            "engine_type": "transformer",
            "device": self.device,
            "num_parameters": num_parameters,
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else 0,
        }
