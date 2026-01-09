/**
 * 元数据动态表单渲染器
 * 支持动态生成表单字段，包括文本输入和多选下拉框
 */

class MetadataFormRenderer {
    constructor() {
        this.configCache = null;
        this.cacheTimestamp = 0;
        this.cacheTTL = 5 * 60 * 1000; // 5分钟缓存
        this.storageKey = 'metadata_config_cache';
    }

    /**
     * 从API获取元数据配置
     * @param {boolean} forceRefresh - 是否强制刷新
     * @returns {Promise<Array>} 配置数组
     */
    async fetchConfig(forceRefresh = false) {
        // 检查内存缓存
        if (!forceRefresh && this.configCache && this.isCacheValid()) {
            return this.configCache;
        }

        // 检查sessionStorage
        if (!forceRefresh) {
            const cached = this.loadFromSessionStorage();
            if (cached) {
                this.configCache = cached;
                return cached;
            }
        }

        // 从API获取
        try {
            const response = await fetch('/api/metadata/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const configs = await response.json();
            this.configCache = configs;
            this.cacheTimestamp = Date.now();
            this.saveToSessionStorage(configs);
            return configs;
        } catch (error) {
            console.error('获取元数据配置失败:', error);
            // 如果有缓存，返回缓存
            if (this.configCache) {
                return this.configCache;
            }
            throw error;
        }
    }

    /**
     * 检查缓存是否有效
     * @returns {boolean}
     */
    isCacheValid() {
        return Date.now() - this.cacheTimestamp < this.cacheTTL;
    }

    /**
     * 保存到sessionStorage
     * @param {Array} configs
     */
    saveToSessionStorage(configs) {
        try {
            const data = {
                configs: configs,
                timestamp: Date.now()
            };
            sessionStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            console.warn('保存到sessionStorage失败:', e);
        }
    }

    /**
     * 从sessionStorage加载
     * @returns {Array|null}
     */
    loadFromSessionStorage() {
        try {
            const data = sessionStorage.getItem(this.storageKey);
            if (!data) return null;

            const parsed = JSON.parse(data);
            const age = Date.now() - parsed.timestamp;
            
            // 检查缓存是否过期
            if (age > this.cacheTTL) {
                sessionStorage.removeItem(this.storageKey);
                return null;
            }

            this.cacheTimestamp = parsed.timestamp;
            return parsed.configs;
        } catch (e) {
            console.warn('从sessionStorage加载失败:', e);
            return null;
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.configCache = null;
        this.cacheTimestamp = 0;
        sessionStorage.removeItem(this.storageKey);
    }

    /**
     * 渲染表单字段
     * @param {Object} config - 配置对象
     * @param {Object} values - 当前值对象
     * @returns {HTMLElement} 表单字段元素
     */
    renderField(config, values = {}) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = this.getFieldClassName(config);
        fieldDiv.dataset.fieldName = config.field_name;

        // 创建标签
        const label = document.createElement('label');
        label.className = 'form-label';
        label.htmlFor = `field-${config.field_name}`;
        
        // 添加必填标记
        if (config.required) {
            const requiredSpan = document.createElement('span');
            requiredSpan.className = 'text-danger';
            requiredSpan.textContent = ' *';
            label.appendChild(document.createTextNode(config.label));
            label.appendChild(requiredSpan);
        } else {
            label.textContent = config.label;
        }
        
        fieldDiv.appendChild(label);

        // 根据类型创建输入控件
        if (config.type === 'text') {
            fieldDiv.appendChild(this.renderTextField(config, values));
        } else if (config.type === 'multi_select') {
            fieldDiv.appendChild(this.renderMultiSelectField(config, values));
        }

        return fieldDiv;
    }

    /**
     * 渲染文本输入字段
     * @param {Object} config - 配置对象
     * @param {Object} values - 当前值对象
     * @returns {HTMLElement}
     */
    renderTextField(config, values) {
        let input;
        
        // description 字段使用 textarea
        if (config.field_name === 'description') {
            input = document.createElement('textarea');
            input.className = 'form-control';
            input.rows = 8;
            input.style.resize = 'vertical';
            input.style.maxHeight = '300px';
            input.style.overflowY = 'auto';
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
        }
        
        input.id = `field-${config.field_name}`;
        input.name = config.field_name;
        input.required = config.required;
        
        // 设置值
        const value = values[config.field_name] || '';
        if (config.field_name === 'description') {
            input.value = value;
        } else {
            input.value = value;
        }

        // 添加占位符
        if (config.field_name === 'doi') {
            input.placeholder = '10.1016/j.cell.2020.08.036';
        } else if (config.field_name === 'db_id') {
            input.placeholder = 'GSE123456, ENAxxxx, PRJNAxxxx';
        } else if (config.field_name === 'db_link') {
            input.placeholder = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123456';
        } else if (config.field_name === 'authors') {
            input.placeholder = '用分号分隔多个作者';
        } else if (config.field_name === 'journal') {
            input.placeholder = 'Cell, Nature, Science等';
        } else if (config.field_name === 'description') {
            input.placeholder = '详细描述项目背景、实验设计等...';
        } else if (config.field_name === 'tags') {
            input.placeholder = '用逗号分隔多个标签';
        }

        return input;
    }

    /**
     * 渲染多选下拉字段
     * @param {Object} config - 配置对象
     * @param {Object} values - 当前值对象
     * @returns {HTMLElement}
     */
    renderMultiSelectField(config, values) {
        const container = document.createElement('div');
        container.className = 'multi-select-wrapper';
        
        // 创建隐藏的 select 元素（用于表单提交）
        const select = document.createElement('select');
        select.className = 'form-select d-none';
        select.id = `field-${config.field_name}`;
        select.name = config.field_name;
        select.required = config.required;
        select.multiple = true;
        
        // 添加选项
        if (config.parsed_options && config.parsed_options.length > 0) {
            config.parsed_options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.textContent = option;
                select.appendChild(optionElement);
            });
        }
        
        // 设置选中值
        const value = values[config.field_name] || '';
        if (value) {
            const selectedValues = value.split(',').map(v => v.trim());
            Array.from(select.options).forEach(option => {
                if (selectedValues.includes(option.value)) {
                    option.selected = true;
                }
            });
        }
        
        container.appendChild(select);
        
        // 创建自定义多选框界面
        const customMultiSelect = document.createElement('div');
        customMultiSelect.className = 'custom-multi-select-container';
        
        // 创建触发按钮（显示已选项）
        const triggerButton = document.createElement('div');
        triggerButton.className = 'multi-select-trigger form-control';
        triggerButton.style.minHeight = '38px';
        triggerButton.style.cursor = 'pointer';
        triggerButton.style.display = 'flex';
        triggerButton.style.alignItems = 'center';
        triggerButton.style.flexWrap = 'wrap';
        triggerButton.style.gap = '4px';
        triggerButton.style.padding = '6px 12px';
        
        // 更新触发按钮显示
        const updateTrigger = () => {
            const selectedValues = Array.from(select.selectedOptions).map(opt => opt.value);
            triggerButton.innerHTML = '';
            
            if (selectedValues.length === 0) {
                triggerButton.innerHTML = '<span class="text-muted">请选择...</span>';
                return;
            }
            
            selectedValues.forEach(val => {
                const tag = document.createElement('span');
                tag.className = 'selected-tag badge bg-light text-dark border';
                tag.style.fontSize = '12px';
                tag.style.padding = '4px 8px';
                tag.style.margin = '2px';
                tag.textContent = val;
                
                // 删除按钮
                const removeBtn = document.createElement('span');
                removeBtn.innerHTML = '&times;';
                removeBtn.style.marginLeft = '4px';
                removeBtn.style.cursor = 'pointer';
                removeBtn.style.color = '#6c757d';
                removeBtn.onclick = (e) => {
                    e.stopPropagation();
                    this.removeOption(select, val);
                    updateTrigger();
                };
                
                tag.appendChild(removeBtn);
                triggerButton.appendChild(tag);
            });
        };
        
        // 初始化显示
        updateTrigger();
        
        // 点击触发按钮打开/关闭下拉菜单
        triggerButton.onclick = (e) => {
            e.stopPropagation();
            if (dropdownMenu.style.display === 'none') {
                updateDropdownPosition();
                dropdownMenu.style.display = 'block';
            } else {
                dropdownMenu.style.display = 'none';
            }
        };
        
        // 创建下拉菜单
        const dropdownMenu = document.createElement('div');
        dropdownMenu.className = 'multi-select-dropdown';
        dropdownMenu.style.display = 'none';
        
        // 计算下拉菜单位置
        const updateDropdownPosition = () => {
            const rect = triggerButton.getBoundingClientRect();
            dropdownMenu.style.top = (rect.bottom + window.scrollY + 2) + 'px';
            dropdownMenu.style.left = rect.left + 'px';
            dropdownMenu.style.width = rect.width + 'px';
        };
        
        // 搜索框
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control form-control-sm mb-2';
        searchInput.placeholder = '搜索选项...';
        searchInput.style.marginBottom = '8px';
        searchInput.oninput = (e) => {
            const searchText = e.target.value.toLowerCase();
            const items = dropdownMenu.querySelectorAll('.multi-select-option');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(searchText) ? 'flex' : 'none';
            });
        };
        
        dropdownMenu.appendChild(searchInput);
        
        // 添加选项
        if (config.parsed_options && config.parsed_options.length > 0) {
            config.parsed_options.forEach(option => {
                const optionItem = document.createElement('div');
                optionItem.className = 'multi-select-option d-flex align-items-center';
                optionItem.style.padding = '6px 8px';
                optionItem.style.borderRadius = '4px';
                optionItem.style.cursor = 'pointer';
                optionItem.dataset.value = option;
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input me-2';
                checkbox.value = option;
                checkbox.checked = Array.from(select.selectedOptions).some(opt => opt.value === option);
                checkbox.onclick = (e) => {
                    e.stopPropagation();
                    this.toggleOption(select, option, checkbox.checked);
                    updateTrigger();
                };
                
                const label = document.createElement('span');
                label.textContent = option;
                label.style.flex = '1';
                label.style.fontSize = '14px';
                
                optionItem.appendChild(checkbox);
                optionItem.appendChild(label);
                
                // 点击整个选项
                optionItem.onclick = () => {
                    checkbox.checked = !checkbox.checked;
                    this.toggleOption(select, option, checkbox.checked);
                    updateTrigger();
                };
                
                // 悬停效果
                optionItem.onmouseenter = () => {
                    optionItem.style.backgroundColor = '#f8f9fa';
                };
                optionItem.onmouseleave = () => {
                    optionItem.style.backgroundColor = '';
                };
                
                dropdownMenu.appendChild(optionItem);
            });
        }
        
        // 快捷按钮
        const quickActions = document.createElement('div');
        quickActions.className = 'multi-select-quick-actions d-flex gap-2 mt-2 pt-2 border-top';
        
        const selectAllBtn = document.createElement('button');
        selectAllBtn.type = 'button';
        selectAllBtn.className = 'btn btn-sm btn-outline-primary';
        selectAllBtn.textContent = '全选';
        selectAllBtn.onclick = () => {
            config.parsed_options.forEach(opt => {
                this.toggleOption(select, opt, true);
            });
            updateTrigger();
        };
        
        const clearAllBtn = document.createElement('button');
        clearAllBtn.type = 'button';
        clearAllBtn.className = 'btn btn-sm btn-outline-secondary';
        clearAllBtn.textContent = '清空';
        clearAllBtn.onclick = () => {
            config.parsed_options.forEach(opt => {
                this.toggleOption(select, opt, false);
            });
            updateTrigger();
        };
        
        quickActions.appendChild(selectAllBtn);
        quickActions.appendChild(clearAllBtn);
        dropdownMenu.appendChild(quickActions);
        
        customMultiSelect.appendChild(triggerButton);
        container.appendChild(customMultiSelect);
        document.body.appendChild(dropdownMenu);
        
        // 点击外部关闭下拉菜单
        const closeHandler = (e) => {
            if (!customMultiSelect.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.style.display = 'none';
            }
        };
        
        document.addEventListener('click', closeHandler);
        
        // 窗口滚动和调整大小时更新位置
        const updateOnScroll = () => {
            if (dropdownMenu.style.display !== 'none') {
                updateDropdownPosition();
            }
        };
        window.addEventListener('scroll', updateOnScroll, true);
        window.addEventListener('resize', updateOnScroll);
        
        // 清理事件监听器
        container.addEventListener('remove', () => {
            document.removeEventListener('click', closeHandler);
        }, { once: true });
        
        return container;
    }
    
    /**
     * 切换选项选中状态
     * @param {HTMLSelectElement} select - 原始 select 元素
     * @param {string} value - 选项值
     * @param {boolean} checked - 是否选中
     */
    toggleOption(select, value, checked) {
        Array.from(select.options).forEach(option => {
            if (option.value === value) {
                option.selected = checked;
            }
        });
    }
    
    /**
     * 移除选项
     * @param {HTMLSelectElement} select - 原始 select 元素
     * @param {string} value - 选项值
     */
    removeOption(select, value) {
        Array.from(select.options).forEach(option => {
            if (option.value === value) {
                option.selected = false;
            }
        });
    }
    /**
     * 获取字段容器类名
     * @param {Object} config - 配置对象
     * @returns {string}
     */
    getFieldClassName(config) {
        return '';
    }

    /**
     * 获取字段的行类名
     * @param {Object} config - 配置对象
     * @returns {string}
     */
    getFieldRowClassName(config) {
        return 'mb-3';
    }

    /**
     * 判断字段是否为特殊字段（标题、描述、标签）
     * 这些字段固定位置，不参与排序
     * @param {Object} config - 配置对象
     * @returns {boolean}
     */
    isSpecialField(config) {
        return config.field_name === 'title' || 
               config.field_name === 'description' || 
               config.field_name === 'tags';
    }

    /**
     * 获取特殊字段的显示顺序
     * @param {string} fieldName - 字段名
     * @returns {number} 显示顺序（越小越靠前）
     */
    getSpecialFieldOrder(fieldName) {
        const order = {
            'title': 1,
            'description': 2,
            'tags': 3
        };
        return order[fieldName] || 999;
    }

    /**
     * 渲染完整表单
     * @param {HTMLElement} container - 容器元素
     * @param {Object} values - 当前值对象
     * @param {boolean} forceRefresh - 是否强制刷新配置
     * @returns {Promise<void>}
     */
    async renderForm(container, values = {}, forceRefresh = false) {
        try {
            // 清空容器
            container.innerHTML = '';
            container.className = 'metadata-form-container';

            // 获取配置
            const configs = await this.fetchConfig(forceRefresh);

            if (!configs || configs.length === 0) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-warning';
                alert.textContent = '无法加载元数据配置';
                container.appendChild(alert);
                return;
            }

            // 分组字段
            const specialFields = [];
            const regularFields = [];

            configs.forEach(config => {
                if (this.isSpecialField(config)) {
                    specialFields.push(config);
                } else {
                    regularFields.push(config);
                }
            });

            // 按照特殊字段顺序排序
            specialFields.sort((a, b) => {
                return this.getSpecialFieldOrder(a.field_name) - this.getSpecialFieldOrder(b.field_name);
            });

            // 标题字段（如果存在）
            if (specialFields.some(c => c.field_name === 'title')) {
                const titleConfig = specialFields.find(c => c.field_name === 'title');
                const titleElement = this.renderField(titleConfig, values);
                const titleCol = document.createElement('div');
                titleCol.className = 'col-12 mb-3';
                titleCol.appendChild(titleElement);
                container.appendChild(titleCol);
            }

            // 创建两列布局区域（引文文件 + 普通字段）
            const twoColumnSection = document.createElement('div');
            twoColumnSection.className = 'row';
            
            let currentRow = document.createElement('div');
            currentRow.className = 'row mb-3';

            // 创建引文文件的列（作为第一个字段）
            const citationCol = document.createElement('div');
            citationCol.className = 'col-md-6';
            
            // 创建引文文件的包装器
            const citationWrapper = document.createElement('div');
            citationWrapper.className = 'mb-3';
            
            const citationLabel = document.createElement('label');
            citationLabel.className = 'form-label';
            citationLabel.htmlFor = 'citation-file';
            citationLabel.textContent = '引文文件';
            
            const citationInput = document.createElement('input');
            citationInput.type = 'file';
            citationInput.className = 'form-control';
            citationInput.id = 'citation-file';
            citationInput.name = 'citation-file';
            citationInput.accept = '.enw,.ris';
            
            const citationHelp = document.createElement('div');
            citationHelp.className = 'form-text';
            citationHelp.textContent = '支持EndNote (.enw) 和 RIS 格式文件';
            
            citationWrapper.appendChild(citationLabel);
            citationWrapper.appendChild(citationInput);
            citationWrapper.appendChild(citationHelp);
            citationCol.appendChild(citationWrapper);
            currentRow.appendChild(citationCol);

            // 添加普通字段（按照元数据配置顺序）
            regularFields.forEach((config, index) => {
                const fieldElement = this.renderField(config, values);
                
                // 普通字段使用两列布局
                const col = document.createElement('div');
                col.className = 'col-md-6';
                col.appendChild(fieldElement);
                
                currentRow.appendChild(col);
                
                // 每两个字段换行（引文文件占一个位置，所以需要判断）
                if (currentRow.children.length === 2) {
                    twoColumnSection.appendChild(currentRow);
                    currentRow = document.createElement('div');
                    currentRow.className = 'row mb-3';
                }
            });

            // 添加最后一行（如果有剩余字段）
            if (currentRow.children.length > 0) {
                twoColumnSection.appendChild(currentRow);
            }

            // 如果有两个section，添加分隔线
            if (specialFields.some(c => c.field_name === 'title')) {
                container.appendChild(twoColumnSection);
            }

            // 创建下方字段区域（描述和标签）
            const bottomSection = document.createElement('div');
            bottomSection.className = 'mt-4 pt-4 border-top';
            
            // 项目描述
            if (specialFields.some(c => c.field_name === 'description')) {
                const descConfig = specialFields.find(c => c.field_name === 'description');
                const descElement = this.renderField(descConfig, values);
                const descWrapper = document.createElement('div');
                descWrapper.className = 'mb-3';
                descWrapper.appendChild(descElement);
                bottomSection.appendChild(descWrapper);
            }

            // 标签
            if (specialFields.some(c => c.field_name === 'tags')) {
                const tagsConfig = specialFields.find(c => c.field_name === 'tags');
                const tagsElement = this.renderField(tagsConfig, values);
                const tagsWrapper = document.createElement('div');
                tagsWrapper.className = 'mb-3';
                tagsWrapper.appendChild(tagsElement);
                bottomSection.appendChild(tagsWrapper);
            }

            if (bottomSection.children.length > 0) {
                container.appendChild(bottomSection);
            }

            // 触发自定义事件
            const event = new CustomEvent('metadataFormRendered', {
                detail: { configs, container }
            });
            document.dispatchEvent(event);

        } catch (error) {
            console.error('渲染表单失败:', error);
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger';
            alert.textContent = `渲染表单失败: ${error.message}`;
            container.appendChild(alert);
        }
    }

    /**
     * 收集表单数据
     * @param {HTMLElement} container - 表单容器
     * @returns {Object} 表单数据对象
     */
    collectFormData(container) {
        const data = {};

        // 获取所有多选字段
        const multiSelects = container.querySelectorAll('select[multiple]');
        multiSelects.forEach(select => {
            if (select.name && select.name.trim()) {  // 确保name存在且不为空
                const selectedOptions = Array.from(select.selectedOptions).map(opt => opt.value);
                data[select.name] = selectedOptions.join(',');
            }
        });

        // 获取所有文本字段
        const textInputs = container.querySelectorAll('input[type="text"]');
        textInputs.forEach(input => {
            if (input.name && input.name.trim()) {  // 确保name存在且不为空
                data[input.name] = input.value;
            }
        });

        // 获取所有文本区域（textarea）- 用于description字段
        const textareas = container.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            if (textarea.name && textarea.name.trim()) {  // 确保name存在且不为空
                data[textarea.name] = textarea.value;
            }
        });

        // 处理特殊字段映射
        if (data.db_id !== undefined) {
            data.dbId = data.db_id;
            delete data.db_id;
        }
        if (data.db_link !== undefined) {
            data.dbLink = data.db_link;
            delete data.db_link;
        }
        if (data.data_type !== undefined) {
            data.dataType = data.data_type;
            delete data.data_type;
        }
        if (data.name !== undefined) {
            data.title = data.name;
            delete data.name;
        }

        return data;
    }

    /**
     * 验证表单
     * @param {HTMLElement} container - 表单容器
     * @returns {Object} 验证结果 {valid: boolean, errors: Array}
     */
    validateForm(container) {
        const errors = [];
        
        // 检查必填字段
        const requiredFields = container.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (field.tagName === 'SELECT' && field.multiple) {
                if (field.selectedOptions.length === 0) {
                    const label = container.querySelector(`label[for="${field.id}"]`);
                    const fieldName = label ? label.textContent.replace(' *', '') : field.name;
                    errors.push(`${fieldName} 是必填项`);
                }
            } else if (!field.value.trim()) {
                const label = container.querySelector(`label[for="${field.id}"]`);
                const fieldName = label ? label.textContent.replace(' *', '') : field.name;
                errors.push(`${fieldName} 是必填项`);
            }
        });

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
}

// 创建全局实例
const metadataFormRenderer = new MetadataFormRenderer();

// 导出到全局
window.metadataFormRenderer = metadataFormRenderer;