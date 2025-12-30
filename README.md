# 🚀 Global AI Copilot

**一款可在任意 Windows 应用程序中使用的本地 AI 代码/文本补全工具**

类似 GitHub Copilot，但完全在本地运行，支持所有应用程序。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 特性

- 🔒 **完全本地运行** - 无需网络连接，隐私安全
- 🌐 **跨应用支持** - 在记事本、VS Code、浏览器等任意应用中工作
- ⚡ **高速推理** - 使用 ExLlamaV2 引擎，支持 RTX 50 系列显卡
- 👻 **幽灵文本 UI** - 透明浮动窗口显示建议，不干扰正常操作
- ⌨️ **快捷键操作** - Tab 接受建议，Esc 拒绝

## 📦 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.11+
- **GPU**: NVIDIA 显卡 (支持 CUDA 12.x / 13.x)
- **VRAM**: 建议 8GB+

## 🛠️ 安装

### 1. 克隆仓库

```bash
git clone https://github.com/IX968/-copilot.git
cd -copilot
```

### 2. 创建 Conda 环境

```bash
conda create -n copilot python=3.11 -y
conda activate copilot
```

### 3. 安装 PyTorch (CUDA 版本)

```bash
# CUDA 12.4 (推荐)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 或 Nightly 版本 (RTX 50 系列需要)
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu126
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 安装 ExLlamaV2

```bash
pip install exllamav2
```

> **RTX 50 系列用户**: 可能需要从源码编译 ExLlamaV2，参考 [ExLlamaV2 仓库](https://github.com/turboderp/exllamav2)

## 🚀 使用方法

### 启动程序

```bash
python main_client.py
```

或使用批处理脚本：

```bash
run_copilot.bat
```

### 操作说明

1. **触发补全**: 在任意应用中打字，停顿 300ms 后自动触发 AI 补全
2. **接受建议**: 按 `Tab` 键插入建议文本
3. **拒绝建议**: 按 `Esc` 键或继续打字

## 📁 项目结构

```
global-ai-copilot/
├── main_client.py       # 主程序入口
├── inference_engine.py  # AI 推理引擎 (ExLlamaV2)
├── ctx_provider.py      # 上下文获取 (Windows UI Automation)
├── input_hook.py        # 全局键盘钩子
├── ui_overlay.py        # 透明浮动窗口 (PyQt6)
├── test_caret.py        # 光标位置诊断工具
├── verify_and_setup.py  # 环境验证脚本
├── run_copilot.bat      # 启动脚本
├── requirements.txt     # Python 依赖
└── README.md
```

## ⚙️ 配置

### 更换模型

在 `inference_engine.py` 中修改模型 ID：

```python
class InferenceEngine:
    def __init__(self, model_id="TheMelonGod/Qwen3-1.7B-exl2"):
        # 可替换为其他 ExL2 量化模型
```

### 调整生成参数

```python
self.settings.temperature = 0.4  # 创造性 (0.1-1.0)
self.settings.top_k = 20         # Top-K 采样
self.settings.top_p = 0.8        # Top-P 采样
```

## 🔧 故障排除

### CUDA 相关错误

确保已安装 NVIDIA 驱动和 CUDA Toolkit：

```bash
nvidia-smi  # 检查驱动
nvcc --version  # 检查 CUDA
```

### UI Automation 失败

某些应用可能不完全支持 Windows UI Automation，此时程序会使用鼠标位置作为备用方案。

### 高 DPI 显示问题

程序已自动处理 DPI 缩放，如仍有问题，可调整 `ui_overlay.py` 中的 `devicePixelRatio()` 逻辑。

## 📋 依赖列表

```
torch>=2.0
exllamav2
transformers
huggingface_hub
PyQt6
keyboard
uiautomation
pyperclip
psutil
pywin32
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [ExLlamaV2](https://github.com/turboderp/exllamav2) - 高性能推理引擎
- [Qwen](https://github.com/QwenLM/Qwen) - 优秀的开源语言模型
- [UIAutomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) - Windows UI 自动化库
