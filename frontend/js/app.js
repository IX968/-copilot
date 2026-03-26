// Global AI Copilot - 前端主应用逻辑

// ======================
// 全局状态
// ======================

let config = {};
let wsLog = null;
let refreshInterval = null;

// ======================
// 初始化
// ======================

document.addEventListener('DOMContentLoaded', () => {
    console.log('[App] 初始化...');

    // 初始化导航
    initNavigation();

    // 连接 WebSocket 日志
    connectWebSocket();

    // 加载配置
    loadConfig();

    // 加载状态
    refreshStatus();

    // 定期刷新状态（每 5 秒）
    refreshInterval = setInterval(refreshStatus, 5000);

    // 初始化滑块值显示
    initSliders();

    console.log('[App] 初始化完成');
});

// ======================
// 导航
// ======================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;

            // 更新导航状态
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // 切换页面
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`page-${page}`).classList.add('active');

            // 页面特定加载
            if (page === 'models') {
                loadModels();
            } else if (page === 'memory') {
                loadMemory();
            }
        });
    });
}

// ======================
// WebSocket 日志连接
// ======================

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    wsLog = new WebSocket(wsUrl);

    wsLog.onopen = () => {
        console.log('[WebSocket] 已连接');
        updateApiStatus(true);
        addLogEntry('[系统] 日志服务已连接', 'success');
    };

    wsLog.onclose = () => {
        console.log('[WebSocket] 已断开');
        updateApiStatus(false);
        addLogEntry('[系统] 日志服务断开，尝试重连...', 'error');

        // 5 秒后重连
        setTimeout(connectWebSocket, 5000);
    };

    wsLog.onerror = (error) => {
        console.error('[WebSocket] 错误:', error);
    };

    wsLog.onmessage = (event) => {
        addLogEntry(event.data, 'info');
    };
}

function updateApiStatus(connected) {
    const dot = document.getElementById('apiStatus');
    const text = document.getElementById('apiStatusText');

    if (connected) {
        dot.classList.add('connected');
        text.textContent = '已连接';
    } else {
        dot.classList.remove('connected');
        text.textContent = '断开...';
    }
}

// ======================
// 日志显示
// ======================

function addLogEntry(message, type = 'info') {
    const container = document.getElementById('logContainer');
    if (!container) return;

    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;

    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

function clearLogs() {
    const container = document.getElementById('logContainer');
    if (container) {
        container.innerHTML = '';
    }
}

function exportLogs() {
    const container = document.getElementById('logContainer');
    if (!container) return;
    const text = container.innerText;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `copilot-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// ======================
// 状态刷新
// ======================

async function refreshStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();

        // 更新服务状态
        const serviceStatus = document.getElementById('serviceStatus');
        if (status.engine?.ready) {
            serviceStatus.textContent = '运行中';
            serviceStatus.style.color = 'var(--success)';
        } else {
            serviceStatus.textContent = '未就绪';
            serviceStatus.style.color = 'var(--warning)';
        }

        // 更新运行时间
        const uptimeSeconds = status.api?.uptime_seconds || 0;
        if (uptimeSeconds > 0) {
            const h = Math.floor(uptimeSeconds / 3600);
            const m = Math.floor((uptimeSeconds % 3600) / 60);
            const s = uptimeSeconds % 60;
            let uptimeStr = '';
            if (h > 0) uptimeStr += `${h}h `;
            if (m > 0 || h > 0) uptimeStr += `${m}m `;
            uptimeStr += `${s}s`;
            document.getElementById('serviceUptime').textContent = `运行时间：${uptimeStr}`;
        }

        // 更新 GPU 状态
        if (status.resources?.gpu?.available) {
            const gpu = status.resources.gpu;
            document.getElementById('gpuUsage').textContent = `${gpu.usage_percent || 0}%`;
            document.getElementById('gpuMemory').textContent =
                `显存：${gpu.memory_allocated_gb || 0} / ${gpu.memory_total_gb || 0} GB`;
        }

        // 更新模型状态
        const loadedModel = status.engine?.model_info?.model_path || '--';
        document.getElementById('loadedModel').textContent = loadedModel.split('/').pop() || loadedModel;
        document.getElementById('modelType').textContent = status.engine?.engine_type || '--';

        // 更新统计
        const stats = status.engine?.stats || {};
        document.getElementById('totalRequests').textContent = stats.total_requests || 0;

        if (stats.avg_inference_time) {
            const avgLatency = (stats.avg_inference_time * 1000).toFixed(0);
            document.getElementById('avgLatency').textContent = `平均延迟：${avgLatency} ms`;
        }

    } catch (error) {
        console.error('[Status] 刷新失败:', error);
    }
}

// ======================
// 配置管理
// ======================

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();

        // 填充表单值
        if (config.engine) {
            document.getElementById('engineType').value = config.engine.type || 'transformer';
        }

        if (config.generation) {
            document.getElementById('temperature').value = config.generation.temperature || 0.7;
            document.getElementById('maxTokens').value = config.generation.max_tokens || 64;
            document.getElementById('topK').value = config.generation.top_k || 40;
            document.getElementById('topP').value = config.generation.top_p || 0.9;
        }

        if (config.trigger) {
            document.getElementById('debounceMs').value = config.trigger.debounce_ms || 300;
            document.getElementById('acceptKey').value = config.trigger.accept_key || 'tab';
        }

        // 填充 API 引擎配置
        if (config.engine?.api) {
            document.getElementById('apiBaseUrl').value = config.engine.api.base_url || '';
            document.getElementById('apiModelId').value = config.engine.api.model_id || '';
            // api_key 不回显（安全考虑）
        }

        // 根据当前引擎类型切换 API 配置区显示
        toggleApiConfig();

        // 更新显示值
        updateSliderValues();

    } catch (error) {
        console.error('[Config] 加载失败:', error);
    }
}

function initSliders() {
    const sliders = document.querySelectorAll('input[type="range"]');
    sliders.forEach(slider => {
        slider.addEventListener('input', updateSliderValues);
    });
}

function updateSliderValues() {
    document.getElementById('temperatureValue').textContent = document.getElementById('temperature').value;
    document.getElementById('maxTokensValue').textContent = document.getElementById('maxTokens').value;
    document.getElementById('topKValue').textContent = document.getElementById('topK').value;
    document.getElementById('topPValue').textContent = document.getElementById('topP').value;
    document.getElementById('debounceMsValue').textContent = document.getElementById('debounceMs').value;
}

async function saveConfig() {
    try {
        const updates = [
            { path: 'engine.type', value: document.getElementById('engineType').value },
            { path: 'generation.temperature', value: parseFloat(document.getElementById('temperature').value) },
            { path: 'generation.max_tokens', value: parseInt(document.getElementById('maxTokens').value) },
            { path: 'generation.top_k', value: parseInt(document.getElementById('topK').value) },
            { path: 'generation.top_p', value: parseFloat(document.getElementById('topP').value) },
            { path: 'trigger.debounce_ms', value: parseInt(document.getElementById('debounceMs').value) },
            { path: 'trigger.accept_key', value: document.getElementById('acceptKey').value },
        ];

        // API 引擎配置（始终保存，切换时生效）
        const apiBaseUrl = document.getElementById('apiBaseUrl').value;
        const apiModelId = document.getElementById('apiModelId').value;
        if (apiBaseUrl) updates.push({ path: 'engine.api.base_url', value: apiBaseUrl });
        if (apiModelId) updates.push({ path: 'engine.api.model_id', value: apiModelId });

        // 单次批量请求替代多次循环
        await fetch('/api/config/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ updates }),
        });

        // 保存配置到文件
        await fetch('/api/config/save', { method: 'POST' });

        addLogEntry('[配置] 配置已保存', 'success');
        alert('配置已保存！');

    } catch (error) {
        console.error('[Config] 保存失败:', error);
        addLogEntry('[配置] 保存失败', 'error');
    }
}

async function resetConfig() {
    if (!confirm('确定要重置为默认配置吗？')) return;

    try {
        await fetch('/api/config/reload', { method: 'POST' });
        await loadConfig();
        addLogEntry('[配置] 配置已重置', 'success');
    } catch (error) {
        console.error('[Config] 重置失败:', error);
    }
}

async function reloadConfig() {
    try {
        await fetch('/api/config/reload', { method: 'POST' });
        await loadConfig();
        addLogEntry('[配置] 配置已重新加载', 'success');
    } catch (error) {
        console.error('[Config] 重新加载失败:', error);
    }
}

// ======================
// 模型管理
// ======================

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();

        const tbody = document.getElementById('modelsTableBody');
        if (!tbody) return;

        if (models.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">未发现模型，请扫描模型目录</td></tr>';
            return;
        }

        // 获取已加载模型
        const loadedRes = await fetch('/api/models/loaded');
        const loadedData = await loadedRes.json();
        const loadedModelName = loadedData.model?.name;

        tbody.innerHTML = models.map(model => `
            <tr>
                <td>${model.name}</td>
                <td>${model.type || model.model_type || '-'}</td>
                <td>${model.size_gb} GB</td>
                <td>
                    <span class="status-badge ${model.is_loaded ? 'loaded' : 'unloaded'}">
                        ${model.is_loaded ? '已加载' : '未加载'}
                    </span>
                </td>
                <td>
                    ${model.is_loaded
                        ? `<button class="btn btn-secondary" onclick="unloadModel('${model.name}')">卸载</button>`
                        : `<button class="btn btn-primary" onclick="loadModel('${model.name}')">加载</button>`
                    }
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('[Models] 加载失败:', error);
    }
}

async function scanModels() {
    try {
        addLogEntry('[模型] 开始扫描模型目录...', 'info');

        const response = await fetch('/api/models/scan', { method: 'POST' });
        const result = await response.json();

        addLogEntry(`[模型] 扫描完成，发现 ${result.count} 个模型`, 'success');
        loadModels();

    } catch (error) {
        console.error('[Models] 扫描失败:', error);
        addLogEntry('[模型] 扫描失败', 'error');
    }
}

async function loadModel(modelName) {
    try {
        addLogEntry(`[模型] 正在加载模型：${modelName}...`, 'info');

        const response = await fetch('/api/models/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: modelName, engine_type: document.getElementById('engineType').value }),
        });

        const result = await response.json();

        if (result.success) {
            addLogEntry(`[模型] 模型加载成功：${modelName}`, 'success');
            loadModels();
            setTimeout(refreshStatus, 1000);
        } else {
            addLogEntry(`[模型] 模型加载失败：${result.detail || result.message || '未知错误'}`, 'error');
        }

    } catch (error) {
        console.error('[Models] 加载失败:', error);
        addLogEntry('[模型] 加载失败', 'error');
    }
}

async function unloadModel(modelName) {
    try {
        addLogEntry(`[模型] 正在卸载模型：${modelName}...`, 'info');

        const response = await fetch('/api/models/unload', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            addLogEntry(`[模型] 模型已卸载：${modelName}`, 'success');
            loadModels();
            setTimeout(refreshStatus, 1000);
        } else {
            addLogEntry(`[模型] 卸载失败：${result.message}`, 'error');
        }

    } catch (error) {
        console.error('[Models] 卸载失败:', error);
        addLogEntry('[模型] 卸载失败', 'error');
    }
}

// ======================
// 引擎切换
// ======================

function toggleApiConfig() {
    const engineType = document.getElementById('engineType').value;
    const section = document.getElementById('apiConfigSection');
    if (section) {
        section.style.display = engineType === 'api' ? 'block' : 'none';
    }
}

async function switchEngine() {
    const engineType = document.getElementById('engineType').value;
    const statusEl = document.getElementById('switchStatus');
    statusEl.textContent = '切换中...';
    statusEl.style.color = 'var(--text-secondary)';

    const body = { engine_type: engineType };

    if (engineType === 'api') {
        body.api_base_url = document.getElementById('apiBaseUrl').value;
        body.api_key      = document.getElementById('apiKey').value;
        body.api_model_id = document.getElementById('apiModelId').value;
    }

    try {
        const res = await fetch('/api/engines/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const result = await res.json();

        if (result.success) {
            statusEl.textContent = '✓ ' + result.message;
            statusEl.style.color = 'var(--success)';
            addLogEntry(`[引擎] ${result.message}（${result.engine_type}）`, 'success');
            setTimeout(refreshStatus, 1000);
        } else {
            statusEl.textContent = '✗ ' + result.message;
            statusEl.style.color = 'var(--error, #ef4444)';
            addLogEntry(`[引擎] ${result.message}`, 'error');
        }
    } catch (e) {
        statusEl.textContent = '✗ 请求失败';
        statusEl.style.color = 'var(--error, #ef4444)';
        addLogEntry('[引擎] 切换请求失败: ' + e.message, 'error');
    }
}

// ======================
// 记忆库
// ======================

async function loadMemory() {
    const tbody = document.getElementById('memoryTableBody');
    if (!tbody) return;

    try {
        // 加载统计
        const statsRes = await fetch('/api/memory/stats');
        const stats = await statsRes.json();
        const statsEl = document.getElementById('memoryStats');
        if (statsEl) {
            statsEl.textContent = `共 ${stats.total_interactions || 0} 条记录 | 接受率 ${((stats.accept_rate || 0) * 100).toFixed(0)}% | 数据库 ${stats.database_size_mb || 0} MB`;
        }

        // 加载列表
        const response = await fetch('/api/memory?limit=50');
        const interactions = await response.json();

        if (!interactions.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无交互记录</td></tr>';
            return;
        }

        tbody.innerHTML = interactions.map(item => {
            const time = new Date(item.timestamp * 1000).toLocaleString();
            const inputShort = (item.input_context || '').slice(0, 60).replace(/</g, '&lt;');
            const outputShort = (item.output_completion || '').slice(0, 60).replace(/</g, '&lt;');
            return `<tr>
                <td>${time}</td>
                <td>${item.app_name || '--'}</td>
                <td title="${inputShort}">${inputShort}</td>
                <td title="${outputShort}">${outputShort}</td>
                <td><span class="status-badge ${item.accepted ? 'loaded' : 'unloaded'}">${item.accepted ? '已接受' : '已拒绝'}</span></td>
                <td><button class="btn btn-secondary" onclick="deleteMemory(${item.id})" style="padding:2px 8px;font-size:0.8em;">删除</button></td>
            </tr>`;
        }).join('');

    } catch (error) {
        console.error('[Memory] 加载失败:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">加载失败</td></tr>';
    }
}

async function searchMemory() {
    const query = document.getElementById('memorySearchInput').value.trim();
    if (!query) {
        loadMemory();
        return;
    }

    const tbody = document.getElementById('memoryTableBody');
    if (!tbody) return;

    try {
        const response = await fetch('/api/memory/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit: 50 }),
        });
        const results = await response.json();

        if (!results.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state">未找到匹配 "${query}" 的记录</td></tr>`;
            return;
        }

        tbody.innerHTML = results.map(item => {
            const time = new Date(item.timestamp * 1000).toLocaleString();
            const inputShort = (item.input_context || '').slice(0, 60).replace(/</g, '&lt;');
            const outputShort = (item.output_completion || '').slice(0, 60).replace(/</g, '&lt;');
            return `<tr>
                <td>${time}</td>
                <td>${item.app_name || '--'}</td>
                <td title="${inputShort}">${inputShort}</td>
                <td title="${outputShort}">${outputShort}</td>
                <td><span class="status-badge ${item.accepted ? 'loaded' : 'unloaded'}">${item.accepted ? '已接受' : '已拒绝'}</span></td>
                <td><button class="btn btn-secondary" onclick="deleteMemory(${item.id})" style="padding:2px 8px;font-size:0.8em;">删除</button></td>
            </tr>`;
        }).join('');

        addLogEntry(`[记忆] 搜索 "${query}"，找到 ${results.length} 条`, 'info');
    } catch (error) {
        console.error('[Memory] 搜索失败:', error);
        addLogEntry('[记忆] 搜索失败', 'error');
    }
}

async function deleteMemory(id) {
    try {
        const response = await fetch(`/api/memory/${id}`, { method: 'DELETE' });
        const result = await response.json();
        if (result.success) {
            addLogEntry(`[记忆] 记录已删除：${id}`, 'success');
            loadMemory();
        }
    } catch (error) {
        console.error('[Memory] 删除失败:', error);
    }
}

async function clearMemory() {
    if (!confirm('确定要清空所有交互记录吗？此操作不可恢复。')) return;

    try {
        const response = await fetch('/api/memory/clear', { method: 'POST' });
        const result = await response.json();
        if (result.success) {
            addLogEntry('[记忆] 所有记忆已清空', 'success');
            loadMemory();
        }
    } catch (error) {
        console.error('[Memory] 清空失败:', error);
        addLogEntry('[记忆] 清空失败', 'error');
    }
}
