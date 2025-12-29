import sys
import subprocess
import importlib.util

def install_nightly():
    print("Installing PyTorch Nightly (CU126)...")
    # Using cu126 nightly as it is often compatible with 50 series via driver backward compatibility
    # and is more likely to be available than cu128 wheels right now.
    cmd = [
        sys.executable, "-m", "pip", "install", "--pre", 
        "torch", "torchvision", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/nightly/cu126",
        "--force-reinstall"
    ]
    subprocess.check_call(cmd)

def install_deps():
    print("Installing Transformers & AutoGPTQ...")
    cmd = [sys.executable, "-m", "pip", "install", "transformers", "accelerate", "optimum", "auto-gptq", "huggingface_hub", "--upgrade"]
    subprocess.check_call(cmd)

try:
    import torch
    print(f"Current Torch: {torch.__version__}")
    if not torch.cuda.is_available():
        print("CUDA missing. Reinstalling Nightly...")
        install_nightly()
    else:
        print(f"CUDA Ready: {torch.cuda.get_device_name(0)}")
        if "dev" not in torch.__version__:
             print("Not a Nightly build. Reinstalling Nightly just in case...")
             install_nightly()
except Exception as e:
    print(f"Torch Check Failed: {e}. Reinstalling Nightly...")
    install_nightly()

try:
    import transformers
    import auto_gptq
    print("Dependencies Ready.")
except:
    install_deps()

print("SETUP PHASE COMPLETE")
