// ========== 元数据配置管理函数 ==========

/**
 * 判断字段是否为特殊字段（不参与排序）
 * @param {string} fieldName - 字段名
 * @returns {boolean}
 */
function isSpecialField(fieldName) {
    const specialFields = ['title', 'description', 'tags'];
    return specialFields.includes(fieldName);
}

/**
 * 获取特殊字段的显示顺序
 * @param {string} fieldName - 字段名
 * @returns {number} 显示顺序（越小越靠前）
 */
function getSpecialFieldOrder(fieldName) {
    const order = {
        'title': 1,
        'description': 2,
        'tags': 3
    };
    return order[fieldName] || 999;
}

/**
 * 加载元数据配置列表
 */
async function loadMetadataConfigList() {
    const configList = document.getElementById('metadata-config-list');
    
    try {
        const response = await fetch('/api/metadata/config');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const configs = await response.json();
        
        if (!configs || configs.length === 0) {
            configList.innerHTML = '<div class="alert alert-info">暂无配置</div>';
            return;
        }
        
        // 分组字段
        const specialFields = [];
        const regularFields = [];

        configs.forEach(config => {
            if (isSpecialField(config.field_name)) {
                specialFields.push(config);
            } else {
                regularFields.push(config);
            }
        });

        // 特殊字段按照固定顺序排序
        specialFields.sort((a, b) => {
            return getSpecialFieldOrder(a.field_name) - getSpecialFieldOrder(b.field_name);
        });

        // 普通字段按照 sort_order 排序
        regularFields.sort((a, b) => a.sort_order - b.sort_order);

        // 计算显示序号（从DOI开始编号）
        let displayIndex = 1;
        const startIndex = specialFields.length + 1;
        
        // 渲染配置列表
        configList.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>排序</th>
                            <th>字段名</th>
                            <th>标签</th>
                            <th>类型</th>
                            <th>选项</th>
                            <th>必填</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${specialFields.map(config => `
                            <tr class="table-light">
                                <td><span class="badge bg-secondary">固定</span></td>
                                <td><code>${config.field_name}</code></td>
                                <td>${config.label}</td>
                                <td>
                                    <span class="badge ${config.type === 'multi_select' ? 'bg-primary' : 'bg-secondary'}">
                                        ${config.type === 'multi_select' ? '多选' : '文本'}
                                    </span>
                                </td>
                                <td>
                                    ${config.options ? 
                                        `<small class="text-muted">${config.options.substring(0, 50)}${config.options.length > 50 ? '...' : ''}</small>` : 
                                        '-'}
                                </td>
                                <td>
                                    ${config.required ? 
                                        '<span class="badge bg-danger">是</span>' : 
                                        '<span class="badge bg-success">否</span>'}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="editConfig('${config.field_name}')" title="编辑">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="deleteConfig('${config.field_name}')" title="删除">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                        ${regularFields.map(config => {
                            const currentIndex = displayIndex++;
                            return `
                            <tr>
                                <td>
                                    <input type="number" class="form-control form-control-sm" 
                                           id="sort-order-${config.field_name}"
                                           value="${config.sort_order}"
                                           readonly
                                           style="width: 60px; background-color: #f8f9fa; border: 1px solid #ced4da; -moz-appearance: textfield; appearance: none;">
                                </td>
                                <td><code>${config.field_name}</code></td>
                                <td>${config.label}</td>
                                <td>
                                    <span class="badge ${config.type === 'multi_select' ? 'bg-primary' : 'bg-secondary'}">
                                        ${config.type === 'multi_select' ? '多选' : '文本'}
                                    </span>
                                </td>
                                <td>
                                    ${config.parsed_options && config.parsed_options.length > 0 ? 
                                        `<small class="text-muted">${config.parsed_options.join(', ').substring(0, 50)}${config.parsed_options.join(', ').length > 50 ? '...' : ''}</small>` : 
                                        '-'}
                                </td>
                                <td>
                                    ${config.required ? 
                                        '<span class="badge bg-danger">是</span>' : 
                                        '<span class="badge bg-success">否</span>'}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="editConfig('${config.field_name}')" title="编辑">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="deleteConfig('${config.field_name}')" title="删除">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `}).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
    } catch (error) {
        console.error('加载配置失败:', error);
        configList.innerHTML = `<div class="alert alert-danger">加载配置失败: ${error.message}</div>`;
    }
}

/**
 * 刷新元数据配置
 */
async function refreshMetadataConfig() {
    // 清除前端缓存
    metadataFormRenderer.clearCache();
    
    // 刷新后端缓存
    try {
        const response = await fetch('/api/metadata/config/refresh', {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('刷新后端缓存失败:', error);
        showAlert('刷新后端缓存失败', 'warning');
    }
    
    // 重新加载配置列表
    await loadMetadataConfigList();
    
    showAlert('配置已刷新', 'success');
}

/**
 * 显示添加配置模态框
 */
function showAddConfigModal() {
    // 创建模态框HTML
    const modalHtml = `
        <div class="modal fade" id="configModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加元数据字段</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="config-form">
                            <div class="mb-3">
                                <label for="config-field-name" class="form-label">字段名 *</label>
                                <input type="text" class="form-control" id="config-field-name" required
                                       placeholder="例如: custom_field">
                                <div class="form-text">只能包含字母、数字和下划线</div>
                            </div>
                            <div class="mb-3">
                                <label for="config-label" class="form-label">标签 *</label>
                                <input type="text" class="form-control" id="config-label" required
                                       placeholder="例如: 自定义字段">
                            </div>
                            <div class="mb-3">
                                <label for="config-type" class="form-label">类型 *</label>
                                <select class="form-select" id="config-type" required>
                                    <option value="text">文本</option>
                                    <option value="multi_select">多选</option>
                                </select>
                            </div>
                            <div class="mb-3" id="options-container" style="display: none;">
                                <label for="config-options" class="form-label">选项 *</label>
                                <textarea class="form-control" id="config-options" rows="3"
                                          placeholder="选项1,选项2,选项3"></textarea>
                                <div class="form-text">用逗号分隔多个选项</div>
                            </div>
                            <div class="mb-3">
                                <label for="config-sort-order" class="form-label">排序</label>
                                <input type="number" class="form-control" id="config-sort-order" value="0">
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="config-required">
                                <label class="form-check-label" for="config-required">必填字段</label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="saveConfig()">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加模态框到页面
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('configModal'));
    modal.show();
    
    // 监听类型变化
    document.getElementById('config-type').addEventListener('change', function() {
        const optionsContainer = document.getElementById('options-container');
        if (this.value === 'multi_select') {
            optionsContainer.style.display = 'block';
        } else {
            optionsContainer.style.display = 'none';
        }
    });
    
    // 模态框关闭时移除
    document.getElementById('configModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    }, { once: true });
}

/**
 * 编辑配置
 */
async function editConfig(fieldName) {
    try {
        // 获取当前配置
        const response = await fetch(`/api/metadata/config/${fieldName}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const config = await response.json();
        
        // 创建编辑模态框HTML
        const modalHtml = `
            <div class="modal fade" id="editConfigModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">编辑元数据字段</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="edit-config-form">
                                <div class="mb-3">
                                    <label for="edit-config-field-name" class="form-label">字段名 *</label>
                                    <input type="text" class="form-control" id="edit-config-field-name" 
                                           value="${config.field_name}" readonly
                                           style="background-color: #f8f9fa;">
                                    <div class="form-text">字段名不可修改</div>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-config-label" class="form-label">标签 *</label>
                                    <input type="text" class="form-control" id="edit-config-label" 
                                           value="${config.label}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-config-type" class="form-label">类型 *</label>
                                    <select class="form-select" id="edit-config-type" required>
                                        <option value="text" ${config.type === 'text' ? 'selected' : ''}>文本</option>
                                        <option value="multi_select" ${config.type === 'multi_select' ? 'selected' : ''}>多选</option>
                                    </select>
                                </div>
                                <div class="mb-3" id="edit-options-container" style="display: ${config.type === 'multi_select' ? 'block' : 'none'};">
                                    <label for="edit-config-options" class="form-label">选项 *</label>
                                    <textarea class="form-control" id="edit-config-options" rows="3"
                                              placeholder="选项1,选项2,选项3">${config.parsed_options ? config.parsed_options.join(', ') : ''}</textarea>
                                    <div class="form-text">用逗号分隔多个选项</div>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-config-sort-order" class="form-label">排序</label>
                                    <input type="number" class="form-control" id="edit-config-sort-order" 
                                           value="${config.sort_order}" readonly>
                                </div>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="edit-config-required" 
                                           ${config.required ? 'checked' : ''}>
                                    <label class="form-check-label" for="edit-config-required">必填字段</label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" onclick="saveEditConfig('${fieldName}')">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加模态框到页面
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('editConfigModal'));
        modal.show();
        
        // 监听类型变化
        document.getElementById('edit-config-type').addEventListener('change', function() {
            const optionsContainer = document.getElementById('edit-options-container');
            if (this.value === 'multi_select') {
                optionsContainer.style.display = 'block';
            } else {
                optionsContainer.style.display = 'none';
            }
        });
        
        // 模态框关闭时移除
        document.getElementById('editConfigModal').addEventListener('hidden.bs.modal', function() {
            modalContainer.remove();
        }, { once: true });
        
    } catch (error) {
        console.error('加载配置失败:', error);
        showAlert(`加载配置失败: ${error.message}`, 'danger');
    }
}

/**
 * 保存编辑的配置
 */
async function saveEditConfig(fieldName) {
    const label = document.getElementById('edit-config-label').value.trim();
    const type = document.getElementById('edit-config-type').value;
    const options = document.getElementById('edit-config-options').value.trim();
    const required = document.getElementById('edit-config-required').checked;
    
    // 验证
    if (!label) {
        showAlert('请填写所有必填字段', 'danger');
        return;
    }
    
    // 如果是多选类型，必须有选项
    if (type === 'multi_select' && !options) {
        showAlert('多选类型必须提供选项', 'danger');
        return;
    }
    
    // 获取当前配置的sort_order
    const response = await fetch('/api/metadata/config');
    const configs = await response.json();
    const currentConfig = configs.find(c => c.field_name === fieldName);
    
    const configData = {
        field_name: fieldName,  // 保持原有的字段名
        label: label,
        type: type,
        options: type === 'multi_select' ? options : null,
        sort_order: currentConfig ? currentConfig.sort_order : 0,
        required: required ? 1 : 0
    };
    
    try {
        const updateResponse = await fetch('/api/metadata/config/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });
        
        if (!updateResponse.ok) {
            throw new Error(`HTTP ${updateResponse.status}: ${updateResponse.statusText}`);
        }
        
        const result = await updateResponse.json();
        
        if (result.success) {
            showAlert('字段更新成功', 'success');

            // 关闭模态框（先移除焦点以避免 aria-hidden 警告）
            const modalElement = document.getElementById('editConfigModal');
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();

            // 刷新配置列表
            await loadMetadataConfigList();
        } else {
            showAlert('更新失败', 'danger');
        }
        
    } catch (error) {
        console.error('保存配置失败:', error);
        showAlert(`保存失败: ${error.message}`, 'danger');
    }
}

/**
 * 删除配置
 */
async function deleteConfig(fieldName) {
    if (!confirm(`确定要删除字段 "${fieldName}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/metadata/config/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ field_name: fieldName })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('字段删除成功', 'success');
            await loadMetadataConfigList();
        } else {
            showAlert('删除失败', 'danger');
        }
        
    } catch (error) {
        console.error('删除配置失败:', error);
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
}

// 全局变量:是否处于编辑排序模式
let isEditingSortOrder = false;

/**
 * 启用排序编辑
 */
function enableSortOrderEdit() {
    isEditingSortOrder = true;
    
    // 更新按钮文本
    const editButton = document.getElementById('edit-sort-order-btn');
    if (editButton) {
        editButton.innerHTML = '<i class="bi bi-save"></i> 保存字段排序';
        editButton.classList.remove('btn-outline-primary');
        editButton.classList.add('btn-success');
    }
    
    // 启用所有排序输入框
    const inputs = document.querySelectorAll('[id^="sort-order-"]');
    inputs.forEach(input => {
        input.readOnly = false;
        input.style.backgroundColor = '#fff';
        input.style.border = '1px solid #0d6efd';
    });
}

/**
 * 保存字段排序
 */
async function saveSortOrders() {
    try {
        const response = await fetch('/api/metadata/config');
        const configs = await response.json();
        
        const updates = [];
        
        configs.forEach(config => {
            if (isSpecialField(config.field_name)) return;
            
            const input = document.getElementById(`sort-order-${config.field_name}`);
            if (input) {
                const newSortOrder = parseInt(input.value);
                if (newSortOrder !== config.sort_order) {
                    updates.push({
                        field_name: config.field_name,
                        label: config.label,
                        type: config.type,
                        options: config.options,
                        required: config.required,
                        sort_order: newSortOrder
                    });
                }
            }
        });
        
        if (updates.length === 0) {
            showAlert('没有需要更新的排序', 'info');
            // 退出编辑模式
            exitSortOrderEditMode();
            return;
        }
        
        // 批量更新
        let successCount = 0;
        for (const update of updates) {
            const res = await fetch('/api/metadata/config/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(update)
            });
            const result = await res.json();
            if (result.success) successCount++;
        }
        
        // 强制刷新缓存
        await fetch('/api/metadata/config/refresh', { method: 'POST' });
        
        // 刷新列表
        await loadMetadataConfigList();
        
        showAlert(`成功更新 ${successCount}/${updates.length} 个字段的排序`, 'success');
        
        // 退出编辑模式
        exitSortOrderEditMode();
        
    } catch (error) {
        console.error('更新排序失败:', error);
        showAlert(`更新排序失败: ${error.message}`, 'danger');
    }
}

/**
 * 退出排序编辑模式
 */
function exitSortOrderEditMode() {
    isEditingSortOrder = false;
    
    // 恢复按钮文本
    const editButton = document.getElementById('edit-sort-order-btn');
    if (editButton) {
        editButton.innerHTML = '<i class="bi bi-sort-numeric-down"></i> 修改字段排序';
        editButton.classList.remove('btn-success');
        editButton.classList.add('btn-outline-primary');
    }
    
    // 禁用所有排序输入框
    const inputs = document.querySelectorAll('[id^="sort-order-"]');
    inputs.forEach(input => {
        input.readOnly = true;
        input.style.backgroundColor = '#f8f9fa';
        input.style.border = '1px solid #ced4da';
    });
}

/**
 * 切换排序编辑模式
 */
function toggleSortOrderEdit() {
    if (isEditingSortOrder) {
        saveSortOrders();
    } else {
        enableSortOrderEdit();
    }
}

/**
 * 上移配置
 */

/**
 * 下移配置
 */

/**
 * 保存配置
 */
async function saveConfig() {
    const fieldName = document.getElementById('config-field-name').value.trim();
    const label = document.getElementById('config-label').value.trim();
    const type = document.getElementById('config-type').value;
    const options = document.getElementById('config-options').value.trim();
    const sortOrder = parseInt(document.getElementById('config-sort-order').value) || 0;
    const required = document.getElementById('config-required').checked;
    
    // 验证
    if (!fieldName || !label) {
        showAlert('请填写所有必填字段', 'danger');
        return;
    }
    
    // 验证字段名格式
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(fieldName)) {
        showAlert('字段名只能包含字母、数字和下划线，且必须以字母或下划线开头', 'danger');
        return;
    }
    
    // 如果是多选类型，必须有选项
    if (type === 'multi_select' && !options) {
        showAlert('多选类型必须提供选项', 'danger');
        return;
    }
    
    const configData = {
        field_name: fieldName,
        label: label,
        type: type,
        options: type === 'multi_select' ? options : null,
        sort_order: sortOrder,
        required: required ? 1 : 0
    };
    
    try {
        const response = await fetch('/api/metadata/config/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('字段添加成功', 'success');

            // 关闭模态框（先移除焦点以避免 aria-hidden 警告）
            const modalElement = document.getElementById('configModal');
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();

            // 刷新配置列表
            await loadMetadataConfigList();
        } else {
            showAlert('添加失败', 'danger');
        }
        
    } catch (error) {
        console.error('保存配置失败:', error);
        showAlert(`保存失败: ${error.message}`, 'danger');
    }
}

/**
 * 加载已删除字段列表
 */
async function loadDeletedFields() {
    const deletedConfigList = document.getElementById('deleted-config-list');
    
    try {
        const response = await fetch('/api/metadata/config/deleted');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const configs = await response.json();
        
        if (!configs || configs.length === 0) {
            deletedConfigList.innerHTML = '<div class="alert alert-info">暂无已删除的字段</div>';
            return;
        }
        
        // 渲染已删除配置列表
        deletedConfigList.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>字段名</th>
                            <th>标签</th>
                            <th>类型</th>
                            <th>选项</th>
                            <th>必填</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${configs.map(config => `
                            <tr>
                                <td><code>${config.field_name}</code></td>
                                <td>${config.label}</td>
                                <td>
                                    <span class="badge ${config.type === 'multi_select' ? 'bg-primary' : 'bg-secondary'}">
                                        ${config.type === 'multi_select' ? '多选' : '文本'}
                                    </span>
                                </td>
                                <td>
                                    ${config.options ? 
                                        `<small class="text-muted">${config.options.substring(0, 50)}${config.options.length > 50 ? '...' : ''}</small>` : 
                                        '-'}
                                </td>
                                <td>
                                    ${config.required ? 
                                        '<span class="badge bg-danger">是</span>' : 
                                        '<span class="badge bg-success">否</span>'}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-success" onclick="restoreConfig('${config.field_name}')" title="恢复">
                                            <i class="bi bi-arrow-counterclockwise"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="permanentDeleteConfig('${config.field_name}')" title="永久删除">
                                            <i class="bi bi-trash3"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
    } catch (error) {
        console.error('加载已删除字段失败:', error);
        deletedConfigList.innerHTML = `<div class="alert alert-danger">加载已删除字段失败: ${error.message}</div>`;
    }
}

/**
 * 恢复已删除的配置
 */
async function restoreConfig(fieldName) {
    if (!confirm(`确定要恢复字段 "${fieldName}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/metadata/config/restore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ field_name: fieldName })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('字段恢复成功', 'success');
            await loadDeletedFields();
            await loadMetadataConfigList();
        } else {
            showAlert('恢复失败', 'danger');
        }
        
    } catch (error) {
        console.error('恢复配置失败:', error);
        showAlert(`恢复失败: ${error.message}`, 'danger');
    }
}

/**
 * 永久删除配置（并清除项目数据）
 */
async function permanentDeleteConfig(fieldName) {
    if (!confirm(`确定要永久删除字段 "${fieldName}" 吗？\n\n此操作将:\n1. 从配置表中彻底删除该字段\n2. 清除所有项目中该字段的数据\n\n此操作不可撤销！`)) {
        return;
    }
    
    // 二次确认
    if (!confirm(`再次确认：您确定要永久删除 "${fieldName}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/metadata/config/permanent-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ field_name: fieldName })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('字段已永久删除，项目数据已清除', 'success');
            await loadDeletedFields();
        } else {
            showAlert('永久删除失败', 'danger');
        }
        
    } catch (error) {
        console.error('永久删除配置失败:', error);
        showAlert(`永久删除失败: ${error.message}`, 'danger');
    }
}