# 🚀 Global AI Copilot

**一款可在任意 Windows 应用程序中使用的本地 AI 代码/文本补全工具**

类似 GitHub Copilot，但完全在本地运行，支持所有应用程序，配备 Web 控制台。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔒 **完全本地运行** | 模型在本地 GPU 上推理，无需网络连接，数据不出机器 |
| 🌐 **跨应用支持** | 在记事本、VS Code、浏览器、Word 等任意 Windows 应用中工作 |
| ⚡ **可插拔引擎** | 支持 Transformer / ExLlamaV2 / 云端 API 三种推理后端 |
| 👻 **幽灵文本 UI** | 透明浮动窗口显示灰色建议文本，不干扰正常操作 |
| ⌨️ **快捷键操作** | Tab 接受建议，Esc 拒绝，300ms 防抖自动触发 |
| 🖥️ **Web 控制台** | 7891 端口一站式管理：模型切换、参数调节、性能监控、日志查看 |
| 🧠 **记忆系统** | SQLite 存储交互历史，上下文增强提升补全质量 |
| 📊 **资源监控** | 实时 GPU 显存、CPU、内存使用监控 |

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Global AI Copilot 系统架构                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Web 控制台 (http://127.0.0.1:7891)                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │ 仪表板   │ │ 模型管理 │ │ 配置中心 │ │ 日志监控 │         │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │                   ↕ HTTP / WebSocket                          │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │              FastAPI 服务器 (7891 端口)                   │  │  │
│  │  │  /api/status  /api/generate  /api/models  /api/config   │  │  │
│  │  │  /ws/logs (WebSocket 实时日志)                           │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↕                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  本地 AI 框架层 (backend/)                     │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │
│  │  │ 引擎管理器  │  │  模型注册表  │  │   资源监控器       │   │  │
│  │  │ 加载/卸载   │  │  扫描/元数据 │  │   GPU/CPU/内存     │   │  │
│  │  │ 健康检查    │  │  版本管理    │  │   温度/显存        │   │  │
│  │  └──────┬──────┘  └──────────────┘  └────────────────────┘   │  │
│  │         │                                                     │  │
│  │         ▼   可插拔引擎接口 (BaseEngine)                        │  │
│  │  ┌──────────────┬──────────────┬──────────────┐               │  │
│  │  │ Transformer  │  ExLlamaV2   │   API 引擎   │               │  │
│  │  │ (HuggingFace)│  (GPTQ/EXL2) │  (OpenAI等)  │               │  │
│  │  └──────────────┴──────────────┴──────────────┘               │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │                  记忆系统 (memory/)                      │  │  │
│  │  │  SQLite 存储 ← 上下文构建器 ← 结构提取器                │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↕                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                桌面补全服务层 (desktop/)                       │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐   │  │
│  │  │ 全局键盘钩子 │  │  上下文获取器 │  │  幽灵文本悬浮窗 │   │  │
│  │  │ 防抖 300ms   │→│  UIA + 鼠标   │→│  PyQt6 透明窗口 │   │  │
│  │  │ Tab/Esc 监听 │  │  进程名识别   │  │  DPI 自适应     │   │  │
│  │  └──────────────┘  └───────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              ↕                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │               数据持久化层 (data/)                             │  │
│  │  SQLite (交互历史)     YAML (配置文件)     日志文件           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户在任意应用中打字
         │
         ▼
┌─────────────────┐   300ms 无按键
│  全局键盘钩子   │──────────────────┐
│  (global_hook)  │                  │ 防抖触发
└─────────────────┘                  ▼
                            ┌─────────────────┐
                            │  上下文获取器   │
                            │ (context_provider)│
                            │                   │
                            │ 1. 获取焦点控件   │
                            │ 2. 读取文本内容   │
                            │ 3. 获取光标位置   │
                            │ 4. 识别应用名称   │
                            └────────┬──────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  POST /api/generate │
                            │  context + 参数  │
                            └────────┬──────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   引擎管理器    │
                            │ (engine_manager) │
                            │                   │
                            │ 1. 记忆增强上下文 │
                            │ 2. 调用推理引擎  │
                            │ 3. 记录统计信息  │
                            └────────┬──────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  幽灵文本悬浮窗 │
                            │ (ghost_overlay)  │
                            │                   │
                            │  在光标位置显示  │
                            │  半透明灰色文本  │
                            └────────┬──────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      │              │              │
                 按 Tab 键      按 Esc 键      继续打字
                      │              │              │
                      ▼              ▼              ▼
              ┌──────────────┐ ┌──────────┐ ┌──────────────┐
              │ 接受补全     │ │ 拒绝补全 │ │  隐藏并重新  │
              │ 剪贴板+Ctrl+V│ │ 隐藏窗口 │ │  触发防抖    │
              └──────────────┘ └──────────┘ └──────────────┘
```

---

## 🧩 技术选型

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| **推理引擎** | Transformers + PyTorch | 兼容性最广，支持 HuggingFace 全部模型，开发效率高 |
| **Web 后端** | FastAPI + Uvicorn | 现代异步框架，自动生成 API 文档，性能优异 |
| **Web 前端** | 原生 HTML/CSS/JS | 零依赖，无需构建工具，部署简单 |
| **桌面 UI** | PyQt6 | 支持透明窗口和 DPI 感知，跨线程信号安全 |
| **键盘钩子** | keyboard 库 | 全局监听，支持按键拦截和模拟输入 |
| **上下文获取** | uiautomation + pywin32 | Windows UI Automation 获取焦点控件文本 |
| **文本插入** | pyperclip + keyboard | 剪贴板 + 模拟 Ctrl+V，兼容所有应用 |
| **数据存储** | SQLite | 零配置，无外部依赖，适合单机场景 |
| **配置格式** | YAML | 支持注释，人类可读，层级清晰 |
| **实时通信** | WebSocket | 日志实时推送到前端控制台 |

---

## 📦 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Windows 10 | Windows 11 |
| **Python** | 3.11+ | 3.11 |
| **GPU** | NVIDIA 4GB+ 显存 (CUDA 12.x) | 8GB+ 显存 (RTX 3060+) |
| **内存** | 8GB | 16GB |
| **磁盘** | 10GB (含模型) | 20GB+ |

> 无 GPU 时可使用 CPU 模式运行（速度较慢）或切换为 API 引擎调用云端模型。

---

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
# 根据你的显卡架构选择 CUDA 版本：

# RTX 50 系列 (Blackwell 架构)，必须使用 CUDA 12.8 (Nightly):
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# RTX 30/40 系列，使用 CUDA 12.4 (推荐):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 仅 CPU (无 GPU):
pip install torch torchvision torchaudio
```

### 4. 安装项目依赖

```bash
# 核心依赖 (推理引擎、桌面服务)
pip install -r requirements.txt

# Web 依赖 (API 服务器、控制台)
pip install -r requirements-web.txt
```

### 5. 准备模型

**方式 A：使用 HuggingFace 模型 ID（自动下载）**

编辑 `config/config.yaml`：
```yaml
engine:
  model_path: "Qwen/Qwen3-1.7B-Base"  # 首次运行自动下载
```

**方式 B：使用本地模型**

将模型文件放入 `models/` 目录，修改配置：
```yaml
engine:
  model_path: "models/your-model-name"
```

---

## 🚀 使用方法

### 快速启动

```bash
run.bat
```

`run.bat` 会自动完成以下步骤：
1. 设置 PYTHONPATH 环境变量
2. 激活 Conda 环境
3. 检查并安装缺失依赖
4. 启动 API 服务器（7891 端口）
5. 等待 API 就绪后启动桌面补全服务

### 分别启动（开发模式）

```bash
# 终端 1：启动 API 服务器
set PYTHONPATH=.
python -m uvicorn backend.api.server:app --host 127.0.0.1 --port 7891

# 终端 2：启动桌面补全服务
set PYTHONPATH=.
python desktop/service.py
```

### Web 控制台

浏览器打开 **http://127.0.0.1:7891**

| 页面 | 功能 |
|------|------|
| **仪表板** | 系统状态总览、GPU/CPU/内存使用率、生成统计 |
| **模型管理** | 扫描本地模型、加载/卸载模型、查看模型元数据 |
| **配置中心** | 调整生成参数（温度、top_k 等）、防抖时间、快捷键 |
| **记忆库** | 查看历史交互记录、搜索、导出 |
| **日志** | 实时系统日志流（WebSocket 推送）|

### 操作说明

| 操作 | 说明 |
|------|------|
| **触发补全** | 在任意应用中打字，停顿 300ms 后自动触发 |
| **接受建议** | 按 `Tab` 键，补全文本通过剪贴板自动插入 |
| **拒绝建议** | 按 `Esc` 键，或继续打字（幽灵文本自动消失）|

---

## 📁 项目结构

```
global-ai-copilot/
│
├── app/                            # 应用入口与配置
│   ├── __init__.py
│   ├── main.py                     # 主启动脚本
│   └── config.py                   # YAML 配置加载器（单例模式）
│
├── backend/                        # 后端 AI 框架
│   ├── __init__.py
│   ├── ai_framework/               # AI 框架核心
│   │   ├── __init__.py
│   │   ├── engine_manager.py       # 引擎生命周期管理（创建/加载/卸载/切换）
│   │   ├── model_registry.py       # 模型注册表（扫描 models/ 目录、元数据管理）
│   │   └── resource_monitor.py     # GPU/CPU/内存 资源监控
│   │
│   ├── engines/                    # 可插拔推理引擎
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseEngine 抽象基类 + 数据类
│   │   └── transformer_engine.py   # HuggingFace Transformers 引擎
│   │
│   ├── memory/                     # 记忆系统
│   │   ├── __init__.py
│   │   ├── storage.py              # SQLite 交互历史存储
│   │   └── context_builder.py      # 基于历史记忆的上下文增强
│   │
│   └── api/                        # FastAPI Web 服务
│       ├── __init__.py
│       ├── server.py               # 服务器入口（lifespan 管理、静态文件、CORS）
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── status.py           # GET  /api/status — 系统状态
│       │   ├── models.py           # CRUD /api/models — 模型管理
│       │   ├── generate.py         # POST /api/generate — 文本生成
│       │   └── config.py           # CRUD /api/config — 配置管理
│       └── websocket/
│           ├── __init__.py
│           └── logs.py             # WS /ws/logs — 实时日志推送
│
├── desktop/                        # 桌面补全服务
│   ├── __init__.py
│   ├── service.py                  # 服务主程序（整合各组件 + pyqtSignal 线程安全）
│   ├── input/
│   │   ├── __init__.py
│   │   ├── global_hook.py          # 全局键盘钩子（300ms 防抖 + Tab/Esc 回调）
│   │   └── context_provider.py     # Windows UIA 上下文获取（文本 + 光标位置）
│   └── output/
│       ├── __init__.py
│       └── ghost_overlay.py        # PyQt6 透明悬浮窗（DPI 自适应）
│
├── frontend/                       # Web 控制台前端
│   ├── index.html                  # 单页应用主页面
│   ├── css/
│   │   └── style.css               # 深色主题 UI 样式
│   ├── js/
│   │   └── app.js                  # 前端交互逻辑（API 调用、WebSocket、表单绑定）
│   └── assets/                     # 静态资源
│
├── config/
│   └── config.yaml                 # 主配置文件（引擎、生成参数、触发、服务器）
│
├── data/                           # 运行时数据（.gitignore）
│   ├── copilot.db                  # SQLite 数据库
│   ├── cache/                      # 模型缓存
│   └── logs/                       # 日志文件
│
├── models/                         # 本地模型目录
│
├── PROJECT_STATUS.md               # 项目进度总览
├── NEXT_ACTIONS.md                 # 下一步行动计划
├── DECISIONS.md                    # 关键决策记录
├── AI_RULES.md                     # AI 编程助手工作规则
│
├── run.bat                         # Windows 一键启动脚本
├── requirements.txt                # 核心 Python 依赖
├── requirements-web.txt            # Web 服务依赖
├── LICENSE                         # MIT 许可证
└── README.md                       # 本文件
```

---

## 🔌 API 接口文档

启动服务器后访问 **http://127.0.0.1:7891/api/docs** 查看交互式 Swagger 文档。

### 核心接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/status` | 系统状态（引擎 + GPU + 统计） |
| `GET` | `/api/status/gpu` | GPU 状态详情 |
| `POST` | `/api/generate` | 生成文本补全 |
| `POST` | `/api/generate/stream` | 流式生成（SSE） |
| `GET` | `/api/models` | 获取可用模型列表 |
| `POST` | `/api/models/scan` | 扫描模型目录 |
| `POST` | `/api/models/load` | 加载模型 |
| `POST` | `/api/models/unload` | 卸载模型 |
| `GET` | `/api/models/loaded` | 获取当前已加载模型 |
| `GET` | `/api/config` | 获取完整配置 |
| `POST` | `/api/config` | 更新单个配置项 |
| `POST` | `/api/config/batch` | 批量更新配置 |
| `POST` | `/api/config/save` | 保存配置到文件 |
| `POST` | `/api/config/reload` | 重新加载配置文件 |
| `WS` | `/ws/logs` | 实时日志推送 |

### 生成接口示例

**请求：**
```json
POST /api/generate
{
    "context": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return ",
    "max_tokens": 64,
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9
}
```

**响应：**
```json
{
    "text": "fibonacci(n-1) + fibonacci(n-2)",
    "tokens_generated": 12,
    "inference_time": 0.83,
    "tokens_per_second": 14.5,
    "success": true
}
```

---

## ⚙️ 配置说明

编辑 `config/config.yaml`，所有配置均可通过 Web 控制台在线修改。

```yaml
# ===== AI 引擎 =====
engine:
  type: transformer        # transformer | exllama | api
  model_path: "Qwen/Qwen3-1.7B-Base"
  api:                      # type=api 时使用
    base_url: "https://api.openai.com/v1"
    api_key: ""
    model_id: "gpt-3.5-turbo"

# ===== 生成参数 =====
generation:
  temperature: 0.7          # 创造性 (0.1-2.0)，越高越随机
  max_tokens: 64            # 单次最大生成 token 数
  top_k: 40                 # Top-K 采样，限制候选词数量
  top_p: 0.9                # Top-P 核采样
  repetition_penalty: 1.1   # 重复惩罚，>1 减少重复

# ===== 触发设置 =====
trigger:
  debounce_ms: 300          # 防抖时间（毫秒），用户停顿后触发
  accept_key: tab           # 接受补全的按键
  reject_key: esc           # 拒绝补全的按键
  auto_trigger:
    enabled: true           # 是否启用自动触发
    min_context_length: 3   # 最小上下文长度（字符数）

# ===== Web 服务器 =====
server:
  host: 127.0.0.1
  port: 7891
  reload: false             # 开发模式热重载

# ===== 桌面服务 =====
desktop:
  enabled: true
  ghost_text:
    alpha: 0.8              # 幽灵文本透明度 (0.1-1.0)
    font_size: 14           # 字体大小
    color: "#aaaaaa"        # 文字颜色
  context:
    max_length: 8000        # 最大上下文长度
    use_mouse_position: true

# ===== 记忆系统 =====
memory:
  enabled: true
  db_path: "data/copilot.db"
  max_history: 1000

# ===== 日志 =====
logging:
  level: INFO               # DEBUG | INFO | WARNING | ERROR
  file: "data/logs/copilot.log"
```

---

## ⚙️ 核心机制

### 防抖 (Debounce)

```
用户打字: H  e  l  l  o  _  W  o  r  l  d  [停顿]
           │  │  │  │  │  │  │  │  │  │  │
           ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼
Timer:    [reset][reset][reset]...[reset]    ──→ 300ms 后触发
                                                    │
                                                    ▼
                                               调用 API 生成
```

- 每次按键**重置**定时器，避免每个字母都发请求
- 用户停顿 300ms（可配置）后才触发一次生成请求
- 修饰键（Shift/Ctrl/Alt）不触发防抖

### 线程安全 UI 更新

```
后台线程 (生成补全)          Qt 主线程 (UI 渲染)
      │                           │
      │  _SignalBridge.show_ghost.emit(text, x, y)
      │ ─────────────────────────→ │
      │                            │  overlay.update_ghost_text()
      │                            │  显示幽灵文本
```

使用 PyQt6 的 `pyqtSignal` 机制，确保从后台线程安全更新 UI，避免崩溃。

### 可插拔引擎

```python
# 所有引擎继承 BaseEngine 抽象基类
class BaseEngine(ABC):
    def load_model(self) -> bool: ...
    def unload_model(self): ...
    def generate(self, request) -> GenerationResult: ...

# 切换引擎只需修改配置
engine:
  type: transformer    # → TransformerEngine
  type: exllama        # → ExLlamaEngine (开发中)
  type: api            # → APIEngine (开发中)
```

### 文本插入

```
接受补全 → 保存原剪贴板 → 补全文本写入剪贴板 → 模拟 Ctrl+V → 恢复原剪贴板
```

兼容所有支持粘贴操作的 Windows 应用。

---

## 🔧 故障排除

### API 服务器无法启动

```bash
# 检查端口是否被占用
netstat -ano | findstr :7891

# 更换端口
python -m uvicorn backend.api.server:app --port 8000
```

### 桌面服务无响应

1. 确认 API 服务器已启动且健康：`curl http://127.0.0.1:7891/api/health`
2. `keyboard` 库需要**管理员权限**，尝试以管理员身份运行终端
3. 检查 `config/config.yaml` 中 `desktop.enabled` 是否为 `true`

### GPU 显存不足

1. 使用更小的模型（如 1.7B 参数量）
2. 减少 `generation.max_tokens`
3. 修改 `engine.type: api` 切换为云端推理

### 模型加载失败

1. 检查模型路径是否正确
2. 确认 PyTorch 版本与 CUDA 版本匹配：`python -c "import torch; print(torch.cuda.is_available())"`
3. 查看日志文件 `data/logs/copilot.log` 获取详细错误

### 幽灵文本位置偏移

- 多显示器 DPI 不同时可能有偏移
- 调整 `desktop.context.use_mouse_position` 配置
- 高 DPI 显示器建议设置 Windows 缩放为 100%

---

## 📋 完整依赖列表

### 核心依赖 (requirements.txt)

```
torch>=2.0              # PyTorch 深度学习框架
transformers            # HuggingFace 模型加载和推理
huggingface_hub         # 模型下载管理
accelerate              # 模型加速（device_map 支持）
PyQt6                   # 桌面 UI 框架
keyboard                # 全局键盘钩子
uiautomation            # Windows UI 自动化
pyperclip               # 跨平台剪贴板操作
psutil                  # 系统资源监控
pywin32                 # Windows API 调用
```

### Web 依赖 (requirements-web.txt)

```
fastapi>=0.109.0        # 现代异步 Web 框架
uvicorn[standard]       # ASGI 服务器
python-multipart        # 文件上传支持
pyyaml>=6.0             # YAML 配置解析
httpx>=0.26.0           # 异步 HTTP 客户端
```

---

## 🎖️ 项目定位

**目标赛事**: 中国计算机设计大赛 - AI 应用板块

### 核心差异化

| 维度 | GitHub Copilot | 本项目 |
|------|---------------|--------|
| **运行方式** | 云端推理 | 完全本地 |
| **支持范围** | 仅代码编辑器 | **任意 Windows 应用** |
| **隐私保护** | 代码上传到云端 | 数据不出本机 |
| **网络依赖** | 必须联网 | 离线可用 |
| **成本** | 付费订阅 | 完全免费 |
| **可定制性** | 不可控 | 模型/参数/引擎均可配置 |

### 技术亮点

1. **全局跨应用补全** — Windows UI Automation 实现任意应用文本获取
2. **可插拔引擎架构** — BaseEngine 抽象基类，一行配置切换引擎
3. **Web 控制台** — FastAPI + WebSocket 实时管理和监控
4. **防抖机制** — 智能触发，避免资源浪费
5. **记忆系统** — SQLite 存储，上下文增强提升补全质量
6. **线程安全 UI** — pyqtSignal 桥接后台推理与前端渲染

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [Qwen](https://github.com/QwenLM/Qwen) — 通义千问系列模型
- [ExLlamaV2](https://github.com/turboderp/exllamav2) — 高性能量化推理
- [FastAPI](https://fastapi.tiangolo.com/) — 现代 Web 框架
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Python Qt 绑定
- [UIAutomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) — Windows UI 自动化
