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
    alert('导出功能开发中...');
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
            body: JSON.stringify({ model_name: modelName }),
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
// 记忆库
// ======================

function loadMemory() {
    // TODO: 实现记忆系统后填充数据
    const tbody = document.getElementById('memoryTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">记忆功能开发中...</td></tr>';
    }
}
