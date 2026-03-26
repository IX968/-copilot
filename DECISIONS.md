# 📝 关键决策记录 (ADR - Architecture Decision Records)

**最后更新**: 2026-03-23

---

## [2026-03-23] 完整架构重构：Web 控制台 + 本地 AI 框架

**状态**: ✅ 已批准，待实施
**决策者**: 项目负责人

### 背景
项目需要从 MVP 升级为完整的本地 AI 框架，包含：
1. Web 控制台（7891 端口）用于模型管理、配置、监控
2. 桌面补全服务（全局钩子 + 幽灵文本）
3. 记忆系统（存储交互历史，提取思想/变量/环境结构）
4. 多引擎支持（Transformer / ExLlamaV2 / API）

### 决策

#### 1. 技术栈选择
| 组件 | 选择 | 理由 |
|------|------|------|
| **Web 后端** | FastAPI + Uvicorn | 现代异步、自动 API 文档、性能优秀 |
| **Web 前端** | 原生 HTML/JS/CSS | 零依赖、简单、易于内嵌部署 |
| **配置文件** | YAML | 支持注释、人类友好、层次清晰 |
| **数据库** | SQLite | 轻量、无需额外服务、支持复杂查询 |
| **WebSocket** | 启用 | 实时日志推送、事件通知 |

#### 2. 架构设计
```
Web 控制台 (7891) ←→ FastAPI Server ←→ AI 引擎工厂 ←→ 推理引擎
                                              ↓
桌面服务 ←→ 全局钩子 + 上下文获取 ←→ (调用本地 API)
                                              ↓
                                        SQLite 记忆库
```

#### 3. 目录结构
```
app/           # 主应用包
backend/       # AI 框架后端（引擎管理、记忆系统、Web API）
frontend/      # Web 控制台静态文件
desktop/       # 桌面补全服务
models/        # 模型文件目录
data/          # 数据持久化（SQLite + 缓存 + 日志）
config/        # YAML 配置文件
```

#### 4. 核心功能
- **引擎工厂模式**: 支持运行时切换 Transformer/ExLlamaV2/API
- **记忆系统**: 每次交互存储，定期提取结构（思想/变量/环境）
- **配置中心**: Web 界面调整参数，实时生效
- **监控面板**: GPU 状态、显存占用、请求统计、性能图表

### 防抖机制设计
**全局键盘监听时，用户打字不立即请求，而是等待停顿后触发。**

```python
# global_hook.py 中添加
class InputHook:
    def __init__(self, debounce_ms=300):
        self.debounce_timer = None
        self.debounce_ms = debounce_ms
        self.last_key_time = 0

    def _on_key_event(self, event):
        # 取消之前的定时器
        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.last_key_time = time.time()

        # 200-300ms 后触发（用户停顿时）
        self.debounce_timer = threading.Timer(
            self.debounce_ms / 1000,
            self._trigger_completion
        )
        self.debounce_timer.start()
```

### 后果
- ✅ 架构清晰，模块解耦
- ✅ Web 控制台便于演示和管理
- ✅ 记忆系统增强上下文质量
- ⚠️ 开发周期增加至 7-10 天
- ⚠️ 需要学习 FastAPI 和前端开发

### 实施计划
见 `NEXT_ACTIONS.md` 详细任务列表

---

## [2026-03-22] 创建项目管理四文档

**状态**: ✅ 已执行
**决策者**: 项目负责人

### 背景
项目从实验阶段进入 MVP，需要规范化管理以便后续重构和参赛准备。

### 决策
创建四个固定文档：
1. `PROJECT_STATUS.md` - 项目总览
2. `NEXT_ACTIONS.md` - 行动计划
3. `DECISIONS.md` - 决策记录
4. `AI_RULES.md` - AI 编程规则

### 理由
- 避免遗忘决策原因
- 便于新成员（或 AI 助手）快速理解
- 参赛时需要完整文档链

---

## [2026-03-xx] 回退到鼠标位置获取光标

**状态**: ✅ 已执行
**决策者**: 开发团队

### 背景
尝试通过 UI Automation 和 Win32 API 获取精确光标位置，但遇到以下问题：
- DPI 缩放导致坐标偏移
- 某些应用（VS Code、浏览器）返回空值
- `GetCaretPos()` 在非标准文本框失效

### 决策
**使用鼠标位置 + 固定偏移 (15,15) 作为光标位置**

### 理由
- 鼠标位置始终可靠
- 用户视线自然跟随鼠标
- 简化代码，减少兼容性处理

### 后果
- ✅ 稳定性大幅提升
- ⚠️ 精确度略有损失（可接受）

---

## [2026-03-xx] 注释改为中文

**状态**: ✅ 已执行
**决策者**: 开发团队

### 背景
项目可能参加中国计算机设计大赛，需要全中文文档和代码注释。

### 决策
将所有代码注释从英文/中英混合改为纯中文。

### 理由
- 参赛评分标准偏好本地化
- 便于中文评审理解代码
- 团队主要使用中文沟通

---

## [2026-03-xx] 使用 Transformers 而非 ExLlamaV2

**状态**: ⚠️ 临时决策
**决策者**: 开发团队

### 背景
README 提到使用 ExLlamaV2，但实际代码使用 Transformers。

### 决策
**当前保持 Transformers，参赛前再评估是否迁移**

### 理由
- Transformers 稳定性更好
- ExLlamaV2 需要额外编译（RTX 50 系列兼容性复杂）
- MVP 阶段优先保证功能可用

### 待决策
参赛前是否需要 ExLlamaV2 的性能优势作为亮点？

---

## [2026-03-xx] 静默失败策略

**状态**: ✅ 已执行
**决策者**: 开发团队

### 背景
上下文获取可能因应用不兼容而失败。

### 决策
**所有异常捕获后返回默认值，不中断主程序**

```python
try:
    # 尝试获取上下文
except Exception:
    return None, 0, 0, "Error"
```

### 理由
- 保证全局钩子不崩溃
- 用户体验优先（宁可无补全，不可卡死）
- 日志已通过 print 输出供调试

---

## [2026-03-23] 防抖机制设计

**状态**: ✅ 已实施
**决策者**: 项目负责人

### 背景
全局监听键盘时，不能每敲一个字母就发一次请求，需要防抖（Debounce）机制。

### 决策
**在 `desktop/input/global_hook.py` 中实现 200-300ms 防抖**

```python
# 伪代码
def on_key_event(event):
    if self.debounce_timer:
        self.debounce_timer.cancel()

    self.last_key_time = time.time()
    self.debounce_timer = threading.Timer(0.3, self.trigger_completion)
    self.debounce_timer.start()
```

### 配置化
防抖时间可在配置文件和 Web 界面调整：
- 默认值：300ms
- 可调范围：100ms - 1000ms

### 理由
- 避免频繁请求 API
- 只在用户停顿时触发，提升体验
- 减少资源浪费

---

## [2026-03-23] 二轮代码审查修复

**状态**: ✅ 已执行
**决策者**: 开发团队

### 背景
架构重构完成后，用户完成了一轮 bug 修复（lifespan、SignalBridge、回调、批量配置等）。第二轮审查发现 7 个残留问题。

### 修复清单

| Fix | 文件 | 问题 | 决策 |
|-----|------|------|------|
| 1 | `backend/api/websocket/logs.py` | `asyncio.create_task` 在推理线程崩溃 | 用 `try/except RuntimeError` 包裹，非异步上下文静默跳过 |
| 2 | `backend/api/websocket/logs.py` | `setup_log_handler()` reload 时重复添加 | `isinstance` 检查防重复 |
| 3 | `app/main.py` | `sys.path` 添加 `app/` 而非项目根 | 多加一层 `dirname` |
| 4 | `resource_monitor.py` | `torch.cuda.utilization()` 缺 device 参数 | 改为 `utilization(0)` |
| 5 | `resource_monitor.py` | `process.cpu_percent()` 首次返回 0 | 缓存 Process 实例并预热 |
| 6 | `model_registry.py` + 路由 | 每次请求新建 ModelRegistry 实例 | 添加 `get_model_registry()` 单例 |
| 7 | `desktop/service.py` | `_pending_completion` 跨线程竞态 | 添加 `threading.Lock()` |

### 理由
- P0 级（1-3）：不修会崩溃
- P1 级（4-5）：功能不准确
- P2 级（6-7）：性能和安全性优化

---

## [2026-03-23] 第三轮代码审查修复

**状态**: ✅ 已执行
**决策者**: 开发团队

### 背景
二轮修复后进行第三次全面审查，发现 2 个新问题和 1 个已知限制。

### 修复清单

| Fix | 文件 | 问题 | 决策 |
|-----|------|------|------|
| 14 | `frontend/js/app.js` | `loadModel()` 失败时读 `result.detail`，但后端非 HTTPException 返回 `message`，导致前端显示 `undefined` | 统一为 `result.detail \|\| result.message \|\| '未知错误'` |
| 15 | `backend/engines/transformer_engine.py` | `unload_model()` 缺少 `gc.collect()`，`del model` 后 Python GC 不保证立即释放显存，切换模型可能 OOM | 在 `del` 后加 `gc.collect()` 再调 `torch.cuda.empty_cache()` |

### 已知限制（暂不修）

| 问题 | 文件 | 说明 |
|------|------|------|
| generate 路由同步阻塞 | `backend/api/routes/generate.py` | `engine_manager.generate()` 是同步调用，推理期间阻塞整个事件循环。修法是 `asyncio.to_thread()`，但需验证 PyTorch 线程安全性。标记为中期优化项 |

### 理由
- Fix 14：前端错误提示体验问题，用户看到 `undefined` 不友好
- Fix 15：显存管理关键路径，OOM 会导致整个服务不可用

---

## [2026-03-25] 流式生成：打字机效果

**状态**: ✅ 已执行

### 决策
用 `TextIteratorStreamer`（transformers 库）实现真正的逐 token 流式输出。

### 改动文件
| 文件 | 改动 |
|------|------|
| `backend/ai_framework/engine_manager.py` | 新增 `generate_stream`，`yield from` 引擎流式迭代器 |
| `backend/api/routes/generate.py` | `/api/generate/stream` 从伪流式改为真 SSE；用 `run_in_executor` 把阻塞的 `next(gen)` 放线程池，不卡事件循环 |
| `desktop/service.py` | `_fetch_completion` 改调 `/api/generate/stream`，`stream=True`，逐行解析 SSE，每收到 token 立即 emit 更新气泡 |

### 理由
- 原来一口气等全文生成完再显示，体验差
- 打字机效果让用户看到 AI 正在思考，参赛演示效果更好
- `run_in_executor` 是 FastAPI 中跑同步生成器的标准做法

---

## [2026-03-25] run.bat 启动超时修复

**状态**: ✅ 已执行

### 决策
把固定 `timeout /t 3` + 单次健康检查，改为最多重试 15 次（每次 1 秒）的循环检查。

### 理由
- API server（uvicorn + 模型加载）在慢机器上可能需要 5-10 秒才就绪
- 原来 3 秒超时会误判失败，提示用户退出
- 重试循环：快则 2 秒通过，慢则最多等 15 秒，不误伤

---

## [2026-03-25] 三引擎模式实现策略

**状态**: ✅ 已执行

### 背景
项目设计时预留了 ExLlamaV2 和 API 引擎接口，engine_manager.py 中均为注释状态，切换时静默回退到 Transformer。

### 决策

#### 1. 不再静默回退
ExLlamaV2/API 引擎创建失败时直接返回 `False`，前端显示明确错误信息。原先的静默回退会让用户误以为已切换成功。

#### 2. ExLlamaV2 引擎：ImportError 时返回 False 而不抛出
```python
try:
    from exllamav2 import ...
except ImportError:
    print("[ExLlamaV2] 库未安装，请运行: pip install exllamav2")
    return False
```
**理由**: exllamav2 需要 CUDA 工具链编译，不是所有环境都有。优雅降级比崩溃好。

#### 3. API 引擎：使用 openai 库而非 requests 直接 HTTP
**理由**: openai 库封装了 SSE 流式、重试、认证等细节，且支持所有 OpenAI 兼容接口（DeepSeek、Qwen API 等）。`requests` 手写 SSE 更易出错。

#### 4. 新增 `POST /api/engines/switch` 端点
**理由**: 引擎切换需要同时更新 config + 切换运行中的引擎实例，是原子操作。现有的 `/api/config/batch` 只写配置，不触发引擎切换。独立端点职责更清晰。

#### 5. 前端：API 配置区条件显示
选"云端 API"时才显示 base_url/api_key/model_id 输入框；切换按钮独立于"保存配置"按钮。
**理由**: api_key 等字段只对 API 引擎有意义，避免混淆。

### 改动文件
| 文件 | 操作 |
|------|------|
| `backend/engines/api_engine.py` | 新建 |
| `backend/engines/exllama_engine.py` | 新建 |
| `backend/api/routes/engines.py` | 新建 |
| `backend/ai_framework/engine_manager.py` | 修改：启用真实引擎 |
| `backend/api/server.py` | 修改：注册 engines 路由 |
| `frontend/index.html` | 修改：API 配置区 + 切换按钮 |
| `frontend/js/app.js` | 修改：toggleApiConfig/switchEngine |
| `requirements.txt` | 修改：添加 openai |

---

## [2026-03-25] 全面代码审查与修复

**状态**: ✅ 已执行

### 背景
三引擎模式实现后，进行全面代码审查，发现 4 个 bug 和 3 个未实装的前端功能。

### Bug 修复

| Bug | 文件 | 严重度 | 修复 |
|-----|------|--------|------|
| `routes/__init__.py` 缺少 engines 导入 | `__init__.py` | P0 崩溃 | 添加 `from . import engines` + `memory` |
| API 引擎 `sk-placeholder` 假密钥 | `api_engine.py:35` | P1 | 移除假密钥，空值时打印警告 |
| `/api/status/memory` 返回硬编码数据 | `status.py:45` | P1 | 接入 `MemoryStorage.get_stats()` |
| `loadModel()` 不传 `engine_type` | `app.js:376` | P2 | 读取 `#engineType` 选择器值传递 |

### 未实装功能补全

| 功能 | 修改 |
|------|------|
| 记忆系统 REST API | 新建 `backend/api/routes/memory.py`，5 个端点 |
| 记忆库前端 UI | 重写 `loadMemory/searchMemory/deleteMemory/clearMemory` |
| 日志导出 | `exportLogs()` 从 alert 改为 Blob 文本下载 |
| 服务运行时间 | server.py 记录 `_server_start_time`，`/api/status` 返回 `uptime_seconds`，前端格式化显示 |

### 决策：不做的事项
- 模型下载/上传：工程量大，与参赛无关
- 使用统计图表：需时序数据采集基础设施
- 语义相似度搜索：需嵌入模型，启发式实现已够用
- AI 模型特征提取：同上
- config.set() 防御性检查：当前代码路径不会触发

---

*新增决策请追加到此文件末尾*
