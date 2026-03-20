import sys
import os
import time
import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 环境引导（针对 BLACKWELL/WINDOWS 的关键步骤）---
def bootstrap_environment():
    # 1. Ninja 路径
    try:
        import ninja
        ninja_path = os.path.dirname(ninja.__file__)
        candidates = [
            os.path.join(ninja_path, 'data', 'bin'),
            os.path.join(sys.prefix, 'Scripts'),
            r'C:\Users\Administrator\AppData\Roaming\Python\Python311\Scripts' 
        ]
        for p in candidates:
            if os.path.exists(os.path.join(p, 'ninja.exe')):
                os.environ['PATH'] = p + os.pathsep + os.environ['PATH']
                break
    except: pass

    # 2. DLL 注入（Torch + CUDA）
    # 确保 torch lib 在 path 中
    torch_lib = os.path.join(os.path.dirname(torch.__file__), 'lib')
    os.environ['PATH'] = torch_lib + os.pathsep + os.environ['PATH']
    try:
        os.add_dll_directory(torch_lib)
    except: pass

    # 查找 CUDA Home 并注入 DLLs
    cuda_candidates = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8",
    ]
    for p in cuda_candidates:
        if os.path.exists(p):
            os.environ['CUDA_HOME'] = p
            bin_path = os.path.join(p, 'bin')
            os.environ['PATH'] = bin_path + os.pathsep + os.environ['PATH']
            try:
                os.add_dll_directory(bin_path)
                # 检查 x64 子目录（v13 特有）
                bin_x64 = os.path.join(bin_path, 'x64')
                if os.path.exists(bin_x64):
                    os.add_dll_directory(bin_x64)
                    os.environ['PATH'] = bin_x64 + os.pathsep + os.environ['PATH']
            except: pass
            break

bootstrap_environment()
# -----------------------------------------------------------

class InferenceEngine:
    def __init__(self, model_id="Qwen/Qwen3-1.7B-Base"):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.is_ready = False

    def load_model(self):
        try:
            print(f"正在解析模型路径：{self.model_id}...")
            print("通过 Transformers 加载基础模型（原生）...")
            
            # 使用 AutoModelForCausalLM 加载
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto", 
                trust_remote_code=True,
                torch_dtype="auto"
            )
            
            print("正在加载分词器...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            self.is_ready = True
            print("推理引擎已就绪（Transformers）。")
            return True

        except Exception as e:
            print(f"严重错误：Transformers 后端加载失败：{e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_completion(self, context_text, max_new_tokens=64):
        if not self.is_ready:
            return None

        # prompt 构建
        # 对于 Base 模型，context 就是 prompt
        # 限制 context 长度以避免 OOM 或处理缓慢
        prompt = context_text[-8000:] 

        t0 = time.time()
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    do_sample=True,
                    top_k=40,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            t1 = time.time()
            
            # 只解码新生成的 token
            input_len = inputs.input_ids.shape[1]
            new_tokens = outputs[0][input_len:]
            
            # Using skip_special_tokens=True to avoid <|endoftext|> spam
            new_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            
            speed = max_new_tokens / (t1 - t0) if (t1 - t0) > 0 else 0
            print(f"生成速度：{speed:.1f} t/s | 输出：{repr(new_text)}")
            
            return new_text
            
        except Exception as e:
            print(f"生成错误：{e}")
            return None

if __name__ == "__main__":
    engine = InferenceEngine()
    if engine.load_model():
        result = engine.generate_completion("def hello_world():\n    print")
        print(f"补全结果：{result}")
