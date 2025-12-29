import sys
import os
import time
import torch
from huggingface_hub import snapshot_download

# --- ENVIRONMENT BOOTSTRAP (CRITICAL FOR BLACKWELL/WINDOWS) ---
def bootstrap_environment():
    # 1. Ninja Path
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

    # 2. DLL Injection (Torch + CUDA)
    # Ensure torch lib is in path
    torch_lib = os.path.join(os.path.dirname(torch.__file__), 'lib')
    os.environ['PATH'] = torch_lib + os.pathsep + os.environ['PATH']
    try:
        os.add_dll_directory(torch_lib)
    except: pass

    # Find CUDA Home & Inject DLLs
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
                # Check for x64 subdirectory (v13 specific)
                bin_x64 = os.path.join(bin_path, 'x64')
                if os.path.exists(bin_x64):
                    os.add_dll_directory(bin_x64)
                    os.environ['PATH'] = bin_x64 + os.pathsep + os.environ['PATH']
            except: pass
            break

bootstrap_environment()
# -----------------------------------------------------------

class InferenceEngine:
    def __init__(self, model_id="Qwen/Qwen2.5-1.5B-Instruct-GPTQ-Int4"):
        self.model_id = model_id
        self.model = None
        self.generator = None
        self.tokenizer = None
        self.is_ready = False

    def load_model(self):
        try:
            print(f"Resolving model path for {self.model_id}...")
            model_path = snapshot_download(repo_id=self.model_id)
            print(f"Model found at: {model_path}")

            from exllamav2 import (
                ExLlamaV2,
                ExLlamaV2Config,
                ExLlamaV2Cache,
                ExLlamaV2Tokenizer,
            )
            from exllamav2.generator import ExLlamaV2BaseGenerator, ExLlamaV2Sampler

            config = ExLlamaV2Config()
            config.model_dir = model_path
            config.prepare()
            
            # 50 Series Optimization/Workaround
            # Try default first, if crash, user handles it (we are in dev mode)
            # config.no_flash_attn = True # Uncomment if necessary

            print("Loading ExLlamaV2 Model...")
            self.model = ExLlamaV2(config)
            self.model.load([12, 24]) # Load balancing for single GPU (just loads all)

            print("Loading Tokenizer...")
            self.tokenizer = ExLlamaV2Tokenizer(config)
            
            print("Initializing Cache...")
            self.cache = ExLlamaV2Cache(self.model)
            
            print("Creating Generator...")
            self.generator = ExLlamaV2BaseGenerator(self.model, self.cache, self.tokenizer)
            self.generator.warmup()
            
            self.settings = ExLlamaV2Sampler.Settings()
            self.settings.temperature = 0.4
            self.settings.top_k = 20
            self.settings.top_p = 0.8
            # self.settings.token_repetition_penalty = 1.1

            self.is_ready = True
            print("Inference Engine Ready (ExLlamaV2).")
            return True

        except Exception as e:
            print(f"CRITICAL: Failed to load ExLlamaV2 backend: {e}")
            print("Note: This often happens if CUDA Toolkit is missing (JIT fail).")
            return False

    def generate_completion(self, context_text, max_new_tokens=32):
        if not self.is_ready:
            return None

        # prompt construction
        # For Copilot, we construct a prompt that asks to complete
        # Simple "User: ... \n Assistant:" might not work for mid-sentence completion.
        # Best for Base/Instruct models used as completion:
        # Just update cache with context and generate.
        
        # Simple logic for now: Treat context as prompt.
        # Trim context to last 1000 chars to fit in context window and be fast
        prompt = context_text[-1000:] 

        t0 = time.time()
        output = self.generator.generate_simple(prompt, num_tokens=max_new_tokens, gen_settings=self.settings)
        t1 = time.time()
        
        # Extract new text
        # output contains prompt + new text
        # Be careful with overlap
        new_text = output[len(prompt):]
        
        speed = max_new_tokens / (t1 - t0) if (t1 - t0) > 0 else 0
        # print(f"Gen Speed: {speed:.1f} t/s")
        
        return new_text

if __name__ == "__main__":
    engine = InferenceEngine()
    if engine.load_model():
        result = engine.generate_completion("def hello_world():\n    print")
        print(f"Completion: {result}")
