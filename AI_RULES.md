# 🤖 AI 编程助手规则

**适用于**: Claude Code、Cursor、GitHub Copilot 等 AI 编程工具
**最后更新**: 2026-03-22

---

## 📁 项目概况

**项目名称**: Global AI Copilot
**类型**: Windows 全局 AI 补全工具
**语言**: Python 3.11+
**核心功能**: 在任意应用中提供本地 AI 代码/文本补全

---

## 📋 AI 助手工作原则

### 0. 每次会话必读（最高优先级）
**每次开始工作前，必须先读取以下四个文件：**
1. `PROJECT_STATUS.md` - 了解项目整体状态
2. `NEXT_ACTIONS.md` - 确认当前优先级
3. `DECISIONS.md` - 避免违反已有决策
4. `AI_RULES.md` - 本规则文件

### 1. 修改前必读
- 修改任何文件前，先 `Read` 该文件
- 先理解现有逻辑，再提出修改建议
- 不要重复造轮子（检查是否有现成函数）

### 2. 保持代码风格
- **注释**: 全中文（简体）
- **命名**: snake_case (函数/变量), CamelCase (类)
- **格式**: 遵循 PEP 8
- **错误处理**: 静默失败，返回默认值

### 2.1 可维护性要求（重要）
- **单一职责**: 每个函数只做一件事，超过 50 行需考虑拆分
- **函数长度**: 单函数不超过 80 行（含注释）
- **参数数量**: 单函数参数不超过 5 个，过多时用配置对象
- **依赖注入**: 模块间通过参数/构造函数传递依赖，避免全局变量
- **类型提示**: 新增函数必须添加类型提示 `def func(x: int) -> str:`
- **文档字符串**: 公共函数必须有 `"""简短描述"""`

### 2.2 可扩展性要求（重要）
- **配置驱动**: 参数写配置文件，不硬编码
- **接口隔离**: 模块间通过接口/协议通信，便于替换实现
- **开放封闭**: 新增功能优先新增类/函数，不修改现有代码
- **工厂模式**: 多实现场景用工厂函数（如多模型切换）
- **事件驱动**: 跨模块通信使用信号/回调，不直接调用

### 3. 最小改动原则
- 只修改与任务直接相关的代码
- 不要主动"顺便"重构或优化
- 除非明确要求，否则不添加新功能

---

## 🛠️ 常用命令与工具

### 文件搜索
```bash
# 找 Python 文件
Glob pattern="**/*.py"

# 找特定内容
Grep pattern="def get_focused_context"
```

### 读取文件
```bash
# 读取完整文件
Read file_path="e:\AI\~copilot\main_client.py"

# 读取部分行
Read file_path="..." offset=50 limit=30
```

### 编辑文件
```bash
# 精确替换
Edit file_path="..." old_string="..." new_string="..."

# 创建新文件
Write file_path="..." content="..."
```

---

## 📦 模块职责速查

| 模块 | 职责 | 关键函数 |
|------|------|----------|
| `main_client.py` | 应用编排 | `GlobalCopilotApp` |
| `inference_engine.py` | AI 推理 | `InferenceEngine.load_model()`, `.generate_completion()` |
| `ui_overlay.py` | UI 显示 | `GhostTextOverlay.update_ghost_text()` |
| `input_hook.py` | 键盘监听 | `InputHook` (全局钩子) |
| `ctx_provider.py` | 上下文获取 | `ContextProvider.get_focused_context()` |

---

## ⚠️ 已知陷阱

### 1. 不要修改的内容
- `model.safetensors` - 模型文件（已.gitignore）
- `__pycache__/` - Python 缓存
- 批处理脚本中的 Conda 环境名

### 2. 特殊处理
- **DPI 缩放**: UI 相关代码已处理，不要改动 `devicePixelRatio()` 逻辑
- **UIA 兼容性**: `ctx_provider` 有多重备用方案，不要简化异常处理
- **键盘钩子**: `suppress=True` 可能全局阻塞按键，谨慎修改

### 3. 性能敏感区
- `input_hook` 的防抖逻辑（300ms）
- `ctx_provider` 的文本获取（避免遍历全文档）
- UI 线程与后台线程的通信（使用 Qt 信号）

---

## 📝 提交规范

### Commit Message 格式
```
<类型>: <简短描述>

- 变更点 1
- 变更点 2
```

**类型**: `feat` `fix` `docs` `style` `refactor` `test` `chore`

**示例**:
```
fix: 清理 main_client.py 重复导入

- 删除行 12-22 的重复 import
- 保留第 1-10 行的导入
```

---

## 🧪 测试与验证

### 运行项目
```bash
python main_client.py
# 或
run_copilot.bat
```

### 测试光标定位
```bash
python test_caret.py
```

### 验证环境
```bash
python verify_and_setup.py
```

---

## 📚 相关文档

- `PROJECT_STATUS.md` - 项目总览
- `NEXT_ACTIONS.md` - 下一步计划
- `DECISIONS.md` - 关键决策记录
- `README.md` - 安装与使用说明

---

## 🚀 参赛相关

**目标赛事**: 中国计算机设计大赛 - AI 应用板块
**评分重点**:
1. 创新性（全局跨应用是亮点）
2. 实用性（解决实际问题）
3. 完整性（功能闭环 + 文档）
4. 技术含量（AI 应用深度）

**AI 助手注意**: 修改代码时考虑参赛评分标准，优先保证稳定性和演示效果。

---

*AI 助手应在每次会话开始时阅读此文件*
