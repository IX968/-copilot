# 📋 下一步行动

**最后更新**: 2026-03-25
**当前阶段**: 流式生成完成，准备集成测试

---

## ✅ 已完成任务

| 阶段 | 任务 | 状态 |
|------|------|------|
| **阶段一** | 基础架构（目录/配置/引擎基类） | ✅ 完成 |
| **阶段二** | FastAPI 服务器 + API 路由 | ✅ 完成 |
| **阶段三** | Web 前端控制台 | ✅ 完成 |
| **阶段四** | 记忆系统（SQLite） | ✅ 完成 |
| **阶段五** | 桌面服务迁移 + 防抖机制 | ✅ 完成 |
| **阶段六** | 整合（启动脚本/文档） | ✅ 完成 |
| **一轮修复** | lifespan/SignalBridge/回调/批量配置/流式生成 | ✅ 完成 |
| **二轮修复** | asyncio安全/防重复handler/sys.path/utilization/cpu预热/单例/线程锁 | ✅ 完成 |
| **流式生成** | TextIteratorStreamer + SSE真流式 + 桌面逐token更新气泡 | ✅ 完成 |
| **run.bat修复** | API健康检查改为重试循环（最多15秒），不误判慢启动 | ✅ 完成 |

---

## 🔴 下一步：集成测试（优先级高）

### 1. 安装依赖并测试 API 服务器

```bash
pip install -r requirements-web.txt

set PYTHONPATH=.
python -m uvicorn backend.api.server:app --host 127.0.0.1 --port 7891
```

**验证**:
- 访问 http://127.0.0.1:7891 显示前端页面
- 访问 http://127.0.0.1:7891/api/docs 显示 Swagger 文档
- `/api/health` 返回 `{"status": "ok"}`

### 2. 测试桌面服务

```bash
set PYTHONPATH=.
python desktop/service.py
```

**验证**:
- 键盘钩子启动成功
- 打字停顿 300ms 后触发补全
- Tab 接受（剪贴板粘贴）、Esc 拒绝正常

### 3. 完整启动测试

```bash
run.bat
```

**验证**: API + 桌面服务同时启动，Web 控制台可访问

---

## 🟡 中期目标（完善功能）

### 4. 清理旧 MVP 文件

删除根目录残留文件：`main_client.py`, `inference_engine.py`, `ui_overlay.py`, `input_hook.py`, `ctx_provider.py`, `run_copilot.bat`, `run_caret_test.bat`, `0.3.10`, `80`, `__pycache__/`

### 5. 实现 ExLlamaV2 引擎

在 `backend/engines/exllama_engine.py` 实现，继承 `BaseEngine`。

### 6. 实现 API 引擎

在 `backend/engines/api_engine.py` 实现 OpenAI 兼容调用。

### 7. 完善记忆系统 UI

在 `frontend/js/app.js` 的 `loadMemory()` 中接入 `/api/memory` 接口。

---

## 🟢 长期目标（参赛准备）

### 8. 性能对比测试

编写 `scripts/benchmark.py`，对比延迟、速度、显存占用。

### 9. 演示 PPT + 视频

---

## 📝 待办清单

- [ ] 集成测试（API + 桌面服务 + run.bat）
- [ ] 清理旧 MVP 文件
- [ ] 实现 ExLlamaV2 引擎
- [ ] 实现 API 引擎
- [ ] 完善记忆系统 UI
- [ ] 性能测试脚本
- [ ] 参赛 PPT

---

*完成任务后请更新此表格状态*
