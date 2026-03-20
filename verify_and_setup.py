import sys
import subprocess
import importlib.util

def install_nightly():
    print("正在安装 PyTorch 夜间版（CU126）...")
    # 使用 cu126 夜间版，因为它通常与 50 系列向后兼容
    # 而且目前比 cu128 wheels 更可能可用
    cmd = [
        sys.executable, "-m", "pip", "install", "--pre", 
        "torch", "torchvision", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/nightly/cu126",
        "--force-reinstall"
    ]
    subprocess.check_call(cmd)

def install_deps():
    print("正在安装 Transformers 和 AutoGPTQ...")
    cmd = [sys.executable, "-m", "pip", "install", "transformers", "accelerate", "optimum", "auto-gptq", "huggingface_hub", "--upgrade"]
    subprocess.check_call(cmd)

try:
    import torch
    print(f"当前 Torch 版本：{torch.__version__}")
    if not torch.cuda.is_available():
        print("CUDA 缺失，正在重新安装夜间版...")
        install_nightly()
    else:
        print(f"CUDA 已就绪：{torch.cuda.get_device_name(0)}")
        if "dev" not in torch.__version__:
             print("不是夜间版。正在重新安装夜间版以防万一...")
             install_nightly()
except Exception as e:
    print(f"Torch 检查失败：{e}。正在重新安装夜间版...")
    install_nightly()

try:
    import transformers
    import auto_gptq
    print("依赖项已就绪。")
except:
    install_deps()

print("设置阶段完成")
