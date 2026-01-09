// 生物信息学数据管理系统 JavaScript

// 全局变量
let projects = [];
let currentSection = 'dashboard';
let selectedProject = null;
let pendingDownloads = [];
let dataTypeChart = null;

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 加载本地存储的项目数据
    loadProjects();
    
    // 设置导航事件监听
    setupNavigation();
    
    // 设置表单事件监听
    setupForms();
    
    // 初始化仪表板
    updateDashboard();
    
    // 检查待处理的下载
    checkPendingDownloads();
    
    // 设置搜索功能
    setupSearch();
    
    // 设置导入相关事件监听
    setupImportEvents();
}

function setupImportEvents() {
    // 监听项目模式切换
    const newProjectMode = document.getElementById('newProjectMode');
    const existingProjectMode = document.getElementById('existingProjectMode');
    
    if (newProjectMode) {
        newProjectMode.addEventListener('change', function() {
            if (this.checked) toggleProjectMode('new');
        });
    }
    
    if (existingProjectMode) {
        existingProjectMode.addEventListener('change', function() {
            if (this.checked) toggleProjectMode('existing');
        });
    }
    
    // 监听已有项目选择
    const selectExistingProject = document.getElementById('select-existing-project');
    if (selectExistingProject) {
        selectExistingProject.addEventListener('change', function() {
            if (this.value) {
                loadProjectData(this.value);
            }
        });
    }
}

// 导航功能
function setupNavigation() {
    const navLinks = document.querySelectorAll('a[data-section]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // 隐藏所有部分
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // 显示选中的部分
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    // 更新导航激活状态
    const navLinks = document.querySelectorAll('a[data-section]');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === sectionName) {
            link.classList.add('active');
        }
    });
    
    currentSection = sectionName;
    
    // 根据部分加载相应数据
    switch(sectionName) {
        case 'dashboard':
            updateDashboard();
            break;
        case 'projects':
            loadProjectsTable();
            break;
        case 'import':
            scanDownloadDirectory();
            break;
        case 'processed':
            loadProcessedData();
            scanAnalysisDirectory();
            updateProjectSelectors();
            break;
        case 'browse':
            loadBrowseData();
            break;
        case 'directory':
            loadDirectoryTree();
            break;
        case 'config':
            loadMetadataConfigList();
            break;
    }
}

// 项目管理功能
function loadProjects() {
    // 从API获取项目列表
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15秒超时

    fetch('/api/projects', {
        signal: controller.signal
    })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            projects = data;
            // 保存到本地存储以确保一致性
            saveProjects();
            // 同时更新仪表板
            updateDashboard();
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('加载项目列表失败:', error);
            // 如果API失败，尝试使用本地存储的缓存
            const stored = localStorage.getItem('biodata_projects');
            if (stored) {
                projects = JSON.parse(stored);
            }
        });
}

function saveProjects() {
    localStorage.setItem('biodata_projects', JSON.stringify(projects));
}

async function createProject() {
    const form = document.getElementById('create-project-form');
    const formContainer = document.getElementById('metadata-form-container');

    // 从动态表单收集数据
    const formData = metadataFormRenderer.collectFormData(formContainer);

    // 验证表单
    const validation = metadataFormRenderer.validateForm(formContainer);
    if (!validation.valid) {
        showAlert('表单验证失败: ' + validation.errors.join(', '), 'danger');
        return;
    }

    const project = {
        title: formData.title,
        doi: formData.doi,
        dbId: formData.dbId,
        dbLink: formData.dbLink,
        dataType: formData.dataType,
        organism: formData.organism,
        authors: formData.authors,
        journal: formData.journal,
        description: formData.description,
        tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
    };

    // 处理引文文件
    const citationFile = document.getElementById('citation-file').files[0];
    if (citationFile) {
        await parseCitationFile(citationFile, project);
    }

    // 保存项目到后端
    try {
        const response = await fetch('/api/create-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(project)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        if (result.success) {
            // 获取完整的项目数据
            const savedProject = await (await fetch(`/api/project/${result.project_id}`)).json();
            projects.push(savedProject);
            saveProjects();

            // 关闭模态框（先移除焦点以避免 aria-hidden 警告）
            const modalElement = document.getElementById('createProjectModal');
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();

            // 重置表单
            form.reset();

            // 刷新显示
            await loadProjects();
            if (currentSection === 'projects') {
                loadProjectsTable();
            }
            updateDashboard();

            showAlert('项目创建成功', 'success');
        }
    } catch (error) {
        console.error('创建项目失败:', error);
        showAlert('创建项目失败: ' + error.message, 'danger');
    }
}

function generateProjectId() {
    const maxId = projects.reduce((max, project) => {
        const idNum = parseInt(project.id.replace('PRJ', ''));
        return idNum > max ? idNum : max;
    }, 0);
    return `PRJ${String(maxId + 1).padStart(3, '0')}`;
}

function sanitizeFileName(fileName) {
    return fileName.replace(/[^a-zA-Z0-9_]/g, '_').substring(0, 50);
}

function createProjectDirectory(project) {
    // 这里应该调用后端API来创建实际的目录和文件
    // 现在只是模拟
    console.log('Creating project directory:', project.path);
    generateProjectMarkdown(project);
}

function generateProjectMarkdown(project) {
    const markdown = `# ${project.title}

## 项目信息
- **项目编号**: ${project.id}
- **DOI**: ${project.doi || 'N/A'}
- **数据库编号**: ${project.dbId || 'N/A'}
- **数据库链接**: ${project.dbLink || 'N/A'}
- **数据类型**: ${getDataTypeLabel(project.dataType)}
- **物种**: ${getOrganismLabel(project.organism)}
- **创建日期**: ${project.createdDate}

## 文献信息
- **作者**: ${project.authors || 'N/A'}
- **期刊**: ${project.journal || 'N/A'}

## 项目描述
${project.description || '暂无描述'}

## 标签
${project.tags.map(tag => `${tag}`).join(', ')}

## 文件结构
\`\`\`
${project.path}/
├── README.md
${project.files.map(file => `├── ${file.name} (${file.size})`).join('\\n')}
\`\`\`

## 文件列表
| 文件名 | 大小 | 类型 | 描述 |
|--------|------|------|------|
${project.files.map(file => `| ${file.name} | ${file.size} | ${file.type} | |`).join('\\n')}

---
*此文件由生物信息学数据管理系统自动生成*
`;

    // 这里应该调用后端API来保存markdown文件
    console.log('Generated markdown for project:', project.id);
    console.log(markdown);
}

function getDataTypeLabel(dataType) {
    // 直接返回数据库中的值，不做任何转换
    return dataType || '未分类';
}

function getOrganismLabel(organism) {
    // 直接返回数据库中的值，不做任何转换
    return organism || '未知';
}

// 引文文件解析
async function parseCitationFile(file, project) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;

            if (file.name.endsWith('.ris')) {
                parseRISFile(content, project);
            } else if (file.name.endsWith('.enw')) {
                parseENWFile(content, project);
            }
            resolve();
        };
        reader.readAsText(file);
    });
}

function parseRISFile(content, project) {
    // RIS格式解析
    const lines = content.split('\n');
    const fields = {};
    
    lines.forEach(line => {
        const match = line.match(/^([A-Z]{2})\s+-\s+(.+)$/);
        if (match) {
            const [, tag, value] = match;
            fields[tag] = value;
        }
    });
    
    // 提取信息并更新项目
    if (fields.TI) project.title = fields.TI;
    if (fields.AU) project.authors = fields.AU.replace(/ and /g, '; ');
    if (fields.JO) project.journal = fields.JO;
    if (fields.DO) project.doi = fields.DO;
    if (fields.AB) project.description = fields.AB;
}

function parseENWFile(content, project) {
    // EndNote格式解析
    const lines = content.split('\n');
    const fields = {};
    
    lines.forEach(line => {
        const match = line.match(/^%([A-Z])\s+(.+)$/);
        if (match) {
            const [, tag, value] = match;
            fields[tag] = value;
        }
    });
    
    // 提取信息并更新项目
    if (fields.T) project.title = fields.T;
    if (fields.A) project.authors = fields.A.replace(/ and /g, '; ');
    if (fields.J) project.journal = fields.J;
    if (fields.R) project.doi = fields.R;
    if (fields.X) project.description = fields.X;
}

// 仪表板功能
function updateDashboard() {
    // 更新统计数据
    document.getElementById('total-projects').textContent = projects.length;

    // 使用中文格式进行匹配,支持逗号分隔的多数据类型
    const transcriptomicsTypes = ['转录组 (RNA-seq)', '单细胞转录组', '空间转录组'];
    const transcriptomicsCount = projects.filter(p => {
        const types = p.dataType ? p.dataType.split(',').map(t => t.trim()) : [];
        return types.some(t => transcriptomicsTypes.includes(t));
    }).length;
    document.getElementById('transcriptomics-count').textContent = transcriptomicsCount;

    const proteomicsTypes = ['蛋白组', '磷酸化组'];
    const proteomicsCount = projects.filter(p => {
        const types = p.dataType ? p.dataType.split(',').map(t => t.trim()) : [];
        return types.some(t => proteomicsTypes.includes(t));
    }).length;
    document.getElementById('proteomics-count').textContent = proteomicsCount;

    const otherTypes = ['质谱流式', '多组学', '其他'];
    const otherCount = projects.filter(p => {
        const types = p.dataType ? p.dataType.split(',').map(t => t.trim()) : [];
        return types.some(t => otherTypes.includes(t));
    }).length;
    document.getElementById('other-count').textContent = otherCount;

    // 更新最近项目列表
    updateRecentProjects();

    // 更新图表
    updateCharts();
}

function updateRecentProjects() {
    const recentProjectsList = document.getElementById('recent-projects-list');
    const recentProjects = projects
        .sort((a, b) => new Date(b.createdDate) - new Date(a.createdDate))
        .slice(0, 5);
    
    if (recentProjects.length === 0) {
        recentProjectsList.innerHTML = '<p class="text-muted">暂无项目</p>';
        return;
    }
    
    recentProjectsList.innerHTML = recentProjects.map(project => `
        <div class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${project.title}</h6>
                <small class="text-muted">${project.createdDate}</small>
            </div>
            <div class="mb-1">
                <span class="badge data-type-badge" data-type="${project.dataType}">${getDataTypeLabel(project.dataType)}</span>
                <span class="badge bg-secondary">${project.id}</span>
            </div>
            <p class="mb-1 text-truncate">${project.description || '暂无描述'}</p>
            <small>
                ${project.doi ? `DOI: ${project.doi}` : ''}
                ${project.dbId ? ` | ${project.dbId}` : ''}
            </small>
        </div>
    `).join('');
}

function updateCharts() {
    // 数据类型分布图
    const ctx = document.getElementById('data-type-chart');
    if (ctx) {
        // 销毁现有图表实例
        if (dataTypeChart) {
            dataTypeChart.destroy();
        }
        
        const dataTypeCounts = {};
        projects.forEach(project => {
            dataTypeCounts[project.dataType] = (dataTypeCounts[project.dataType] || 0) + 1;
        });
        
        dataTypeChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(dataTypeCounts).map(type => getDataTypeLabel(type)),
                datasets: [{
                    data: Object.values(dataTypeCounts),
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// 下载目录扫描功能
function checkPendingDownloads() {
    // 这里应该调用后端API来检查下载目录
    // 现在只是模拟
    const pendingCount = Math.floor(Math.random() * 3);
    
    const pendingDiv = document.getElementById('pending-downloads');
    const noPendingDiv = document.getElementById('no-pending');
    
    if (pendingCount > 0) {
        document.getElementById('pending-count').textContent = pendingCount;
        pendingDiv.style.display = 'block';
        noPendingDiv.style.display = 'none';
    } else {
        pendingDiv.style.display = 'none';
        noPendingDiv.style.display = 'block';
    }
}

function scanDownloadDirectory() {
    const resultsDiv = document.getElementById('download-scan-results');
    resultsDiv.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> 正在扫描下载目录...</div>';
    
    // 设置超时处理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
        resultsDiv.innerHTML = '<div class="alert alert-warning">扫描超时，请稍后重试。可能是因为文件数量较多，建议分批处理。</div>';
    }, 25000); // 25秒超时
    
    // 调用后端API扫描目录
    fetch('/api/scan-downloads', {
        signal: controller.signal,
        timeout: 30000
    })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(results => {
            displayScanResults(results);
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('扫描下载目录失败:', error);
            let errorMessage = '扫描下载目录失败';
            if (error.name === 'AbortError') {
                errorMessage = '扫描超时，请稍后重试。可能是因为文件数量较多，建议分批处理。';
            } else if (error.message) {
                errorMessage = '扫描下载目录失败: ' + error.message;
            }
            resultsDiv.innerHTML = `<div class="alert alert-warning">${errorMessage}</div>`;
        });
}

function displayScanResults(results) {
    const resultsDiv = document.getElementById('download-scan-results');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">没有发现待处理的下载文件夹</div>';
        return;
    }
    
    resultsDiv.innerHTML = results.map((result, index) => `
        <div class="scan-result-item">
            <div class="scan-result-header">
                <div class="scan-result-title">${result.name}</div>
                <div>
                    <button class="btn btn-sm btn-outline-primary" onclick="previewImport(${index})">
                        <i class="bi bi-eye"></i> 预览
                    </button>
                    <button class="btn btn-sm btn-success" onclick="importDownload(${index})">
                        <i class="bi bi-download"></i> 导入
                    </button>
                </div>
            </div>
            <div class="scan-result-path">
                <div><strong>相对路径:</strong> <code>downloads/${result.relativePath || result.name}</code></div>
                <div class="text-muted small"><strong>完整路径:</strong> ${result.path}</div>
            </div>
            <div class="scan-result-info">
                <span><i class="bi bi-hdd"></i> ${result.size}</span>
                <span><i class="bi bi-file-earmark"></i> ${result.files} 个文件</span>
                ${result.citationFile ? '<span><i class="bi bi-file-text"></i> 包含引文文件</span>' : ''}
            </div>
            ${result.detectedDOI || result.detectedDbId ? `
                <div class="detected-info">
                    <div class="detected-info-item">
                        <span class="detected-info-label">检测到的DOI:</span>
                        <span class="detected-info-value">${result.detectedDOI || 'N/A'}</span>
                    </div>
                    <div class="detected-info-item">
                        <span class="detected-info-label">检测到的数据库编号:</span>
                        <span class="detected-info-value">${result.detectedDbId || 'N/A'}</span>
                    </div>
                    <div class="detected-info-item">
                        <span class="detected-info-label">检测到的数据类型:</span>
                        <span class="detected-info-value">${getDataTypeLabel(result.detectedType)}</span>
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
    
    pendingDownloads = results;
}

function previewImport(index) {
    const result = pendingDownloads[index];
    
    // 检查元素是否存在
    const modalElement = document.getElementById('importProjectModal');
    if (!modalElement) {
        console.error('找不到importProjectModal元素');
        showAlert('无法打开预览界面', 'danger');
        return;
    }
    
    // 显示预览模态框
    const modal = new bootstrap.Modal(modalElement);
    
    // 尝试获取内容元素,如果不存在则使用模态框的body
    const content = document.getElementById('import-project-content') || 
                   modalElement.querySelector('.modal-body');
    
    if (!content) {
        console.error('找不到模态框内容元素');
        showAlert('无法显示预览内容', 'danger');
        return;
    }
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>检测到的信息</h6>
                <table class="table table-sm">
                    <tr><td>DOI:</td><td>${result.detectedDOI || '未检测到'}</td></tr>
                    <tr><td>数据库编号:</td><td>${result.detectedDbId || '未检测到'}</td></tr>
                    <tr><td>数据类型:</td><td>${getDataTypeLabel(result.detectedType)}</td></tr>
                    <tr><td>文件大小:</td><td>${result.size}</td></tr>
                    <tr><td>文件数量:</td><td>${result.files}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>项目信息设置</h6>
                <form id="import-project-form">
                    <div class="mb-3">
                        <label class="form-label">项目标题</label>
                        <input type="text" class="form-control" value="${result.name}" id="import-title">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">数据类型</label>
                        <select class="form-select" id="import-data-type">
                            <option value="transcriptomics" ${result.detectedType === 'transcriptomics' ? 'selected' : ''}>转录组</option>
                            <option value="scrna-seq" ${result.detectedType === 'scrna-seq' ? 'selected' : ''}>单细胞转录组</option>
                            <option value="proteomics" ${result.detectedType === 'proteomics' ? 'selected' : ''}>蛋白组</option>
                            <option value="multiomics" ${result.detectedType === 'multiomics' ? 'selected' : ''}>多组学</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">物种</label>
                        <select class="form-select" id="import-organism">
                            <option value="human">人类</option>
                            <option value="mouse">小鼠</option>
                            <option value="rat">大鼠</option>
                        </select>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    modal.show();
}

function importDownload(index) {
    const result = pendingDownloads[index];
    
    // 显示高级导入模态框
    showAdvancedImportModal(result);
}

async function showAdvancedImportModal(downloadResult) {
    try {
        // 检查模态框元素是否存在
        const modalElement = document.getElementById('importProjectModal');
        if (!modalElement) {
            console.error('找不到importProjectModal元素');
            showAlert('无法打开导入界面', 'danger');
            return;
        }

        // 生成新的项目ID
        const newProjectId = generateProjectId();
        const projectIdElement = document.getElementById('import-project-id');
        if (projectIdElement) {
            projectIdElement.value = newProjectId;
        }

        // 设置默认值
        const projectNameElement = document.getElementById('import-project-name');
        if (projectNameElement) {
            projectNameElement.value = downloadResult.name;
        }

        const descElement = document.getElementById('import-description');
        if (descElement) {
            descElement.value = `从下载目录导入，包含 ${downloadResult.files} 个文件，总大小 ${downloadResult.size}`;
        }

        // 重置项目模式选择
        const newProjectMode = document.getElementById('newProjectMode');
        const existingProjectMode = document.getElementById('existingProjectMode');
        const newProjectForm = document.getElementById('newProjectForm');
        const existingProjectForm = document.getElementById('existingProjectForm');
        
        if (newProjectMode) newProjectMode.checked = true;
        if (existingProjectMode) existingProjectMode.checked = false;
        
        // 确保表单元素存在后再切换模式
        if (newProjectForm && existingProjectForm) {
            toggleProjectMode('new');
        }

        // 加载项目列表
        loadExistingProjects();

        // 加载文件列表
        loadFileList(downloadResult.name);

        // 动态生成元数据字段
        await loadImportMetadataFields();

        // 显示模态框
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } catch (error) {
        console.error('显示高级导入模态框失败:', error);
        showAlert('打开导入界面失败: ' + error.message, 'danger');
    }
}

function toggleProjectMode(mode) {
    const newForm = document.getElementById('newProjectForm');
    const existingForm = document.getElementById('existingProjectForm');
    
    if (!newForm || !existingForm) {
        console.error('找不到表单元素');
        return;
    }
    
    if (mode === 'new') {
        newForm.style.display = 'block';
        existingForm.style.display = 'none';
        const projectIdElement = document.getElementById('import-project-id');
        if (projectIdElement) {
            projectIdElement.disabled = false;
        }
    } else {
        newForm.style.display = 'none';
        existingForm.style.display = 'block';
        const projectIdElement = document.getElementById('import-project-id');
        if (projectIdElement) {
            projectIdElement.disabled = true;
        }
    }
}

function loadExistingProjects() {
    fetch('/api/projects')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('select-existing-project');
            select.innerHTML = '<option value="">请选择项目...</option>';
            
            data.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = `${project.id} - ${project.title}`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('加载项目列表失败:', error);
            showAlert('加载项目列表失败', 'danger');
        });
}

async function loadImportMetadataFields() {
    try {
        const response = await fetch('/api/metadata/config');
        const configs = await response.json();
        
        // 分离固定字段和可变字段
        const fixedFields = ['title', 'doi', 'db_id', 'db_link', 'authors', 'journal', 'description', 'tags'];
        const variableFields = configs.filter(config => 
            !fixedFields.includes(config.field_name)
        ).sort((a, b) => a.sort_order - b.sort_order);
        
        // 为新建项目生成表单: 只显示数据类型、物种、样本来源
        const newProjectContainer = document.getElementById('new-project-metadata-fields');
        if (newProjectContainer) {
            newProjectContainer.innerHTML = '';
            const renderer = new MetadataFormRenderer();
            
            // 只添加数据类型、物种、样本来源字段
            const importFields = configs.filter(config => 
                ['data_type', 'organism', 'tissue_type'].includes(config.field_name)
            );
            importFields.forEach(config => {
                const fieldElement = renderer.renderField(config, {});
                newProjectContainer.appendChild(fieldElement);
            });
        }
        
        // 为已有项目生成表单: 前3个可变字段
        const existingProjectContainer = document.getElementById('existing-project-metadata-fields');
        if (existingProjectContainer) {
            existingProjectContainer.innerHTML = '';
            const renderer = new MetadataFormRenderer();
            variableFields.slice(0, 3).forEach(config => {
                const fieldElement = renderer.renderField(config, {});
                existingProjectContainer.appendChild(fieldElement);
            });
        }
    } catch (error) {
        console.error('加载导入元数据字段失败:', error);
    }
}

function loadFileList(folderName) {
    fetch(`/api/list-folder-files?folder=${encodeURIComponent(folderName)}`)
        .then(response => response.json())
        .then(data => {
            const fileList = document.getElementById('import-file-list');
            fileList.innerHTML = '';
            
            if (data.files && data.files.length > 0) {
                data.files.forEach((file, index) => {
                    const fileItem = createFileItem(file, index);
                    fileList.appendChild(fileItem);
                });
            } else {
                fileList.innerHTML = '<div class="alert alert-info">未找到文件</div>';
            }
        })
        .catch(error => {
            console.error('加载文件列表失败:', error);
            document.getElementById('import-file-list').innerHTML = 
                '<div class="alert alert-danger">加载文件列表失败</div>';
        });
}

function createFileItem(file, index) {
    const div = document.createElement('div');
    div.className = 'd-flex align-items-center p-2 border-bottom';
    
    const checkbox = document.createElement('input');
    checkbox.className = 'form-check-input me-3 flex-shrink-0';
    checkbox.type = 'checkbox';
    checkbox.value = file.path;
    checkbox.id = `file-${index}`;
    checkbox.checked = true; // 默认选中所有文件
    
    const label = document.createElement('label');
    label.className = 'flex-grow-1';
    label.htmlFor = `file-${index}`;
    label.style.cursor = 'pointer';
    
    const fileInfo = document.createElement('div');
    fileInfo.className = 'd-flex justify-content-between align-items-center';
    
    const fileName = document.createElement('div');
    fileName.innerHTML = `
        <div class="fw-medium">${file.name}</div>
        <small class="text-muted">${file.relativePath}</small>
    `;
    
    const fileSize = document.createElement('div');
    fileSize.className = 'text-muted small';
    fileSize.textContent = file.size || 'N/A';
    
    fileInfo.appendChild(fileName);
    fileInfo.appendChild(fileSize);
    label.appendChild(fileInfo);
    
    div.appendChild(checkbox);
    div.appendChild(label);
    
    // 点击行切换复选框状态
    div.addEventListener('click', (e) => {
        if (e.target !== checkbox && e.target !== label) {
            checkbox.checked = !checkbox.checked;
        }
    });
    
    return div;
}

function selectAllFiles() {
    const checkboxes = document.querySelectorAll('#import-file-list input[type="checkbox"]');
    checkboxes.forEach(checkbox => checkbox.checked = true);
}

function deselectAllFiles() {
    const checkboxes = document.querySelectorAll('#import-file-list input[type="checkbox"]');
    checkboxes.forEach(checkbox => checkbox.checked = false);
}

// 项目表格功能
function loadProjectsTable() {
    const tbody = document.getElementById('projects-table-body');
    
    if (projects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无项目</td></tr>';
        return;
    }
    
    tbody.innerHTML = projects.map(project => `
        <tr>
            <td><span class="badge bg-primary">${project.id}</span></td>
            <td>
                <a href="#" onclick="showProjectDetail('${project.id}')" class="text-decoration-none">
                    ${project.title}
                </a>
            </td>
            <td><span class="badge data-type-badge" data-type="${project.dataType}">${getDataTypeLabel(project.dataType)}</span></td>
            <td>
                <small>
                    ${project.doi ? `DOI: ${project.doi}<br>` : ''}
                    ${project.dbId ? `${project.dbId}` : ''}
                </small>
            </td>
            <td>${getOrganismLabel(project.organism)}</td>
            <td>${project.createdDate}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="showProjectDetail('${project.id}')" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary" onclick="editProject('${project.id}')" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProject('${project.id}')" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function showProjectDetail(projectId) {
    // 从API获取最新项目数据，而不是依赖缓存
    fetch(`/api/project/${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(project => {
            if (!project) return;
            
            selectedProject = project;
            
            const content = document.getElementById('project-detail-content');
            content.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h4>${project.title}</h4>
                        <div class="mb-3">
                            <span class="badge data-type-badge" data-type="${project.dataType}">${getDataTypeLabel(project.dataType)}</span>
                            <span class="badge bg-secondary">${project.id}</span>
                            <span class="badge bg-info">${getOrganismLabel(project.organism)}</span>
                        </div>
                        
                        <h6>项目信息</h6>
                        <table class="table table-sm">
                            <tr><td>DOI:</td><td>${project.doi || 'N/A'}</td></tr>
                            <tr><td>数据库编号:</td><td>${project.dbId || 'N/A'}</td></tr>
                            <tr><td>数据库链接:</td><td>${project.dbLink ? '<a href="' + project.dbLink + '" target="_blank">' + project.dbLink + '</a>' : 'N/A'}</td></tr>
                            <tr><td>作者:</td><td>${project.authors || 'N/A'}</td></tr>
                            <tr><td>期刊:</td><td>${project.journal || 'N/A'}</td></tr>
                            <tr><td>创建日期:</td><td>${project.createdDate}</td></tr>
                            <tr><td>项目路径:</td><td><code>${project.path}</code></td></tr>
                        </table>
                        
                        <h6>项目描述</h6>
                        <p>${project.description || '暂无描述'}</p>
                        
                        <h6>标签</h6>
                        <div>
                            ${project.tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <h6>文件列表</h6>
                        <div class="list-group">
                            ${project.files.length > 0 ? project.files.map(file => `
                                <div class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-file-earmark me-2"></i>
                                            ${file.name}
                                        </div>
                                        <small class="text-muted">${file.size}</small>
                                    </div>
                                </div>
                            `).join('') : '<p class="text-muted">暂无文件</p>'}
                        </div>
                    </div>
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('projectDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('获取项目详情失败:', error);
            // 如果API失败，回退到缓存数据
            const project = projects.find(p => p.id === projectId);
            if (!project) return;
            
            selectedProject = project;
            
            const content = document.getElementById('project-detail-content');
            content.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h4>${project.title}</h4>
                        <div class="mb-3">
                            <span class="badge data-type-badge" data-type="${project.dataType}">${getDataTypeLabel(project.dataType)}</span>
                            <span class="badge bg-secondary">${project.id}</span>
                            <span class="badge bg-info">${getOrganismLabel(project.organism)}</span>
                        </div>
                        
                        <h6>项目信息</h6>
                        <table class="table table-sm">
                            <tr><td>DOI:</td><td>${project.doi || 'N/A'}</td></tr>
                            <tr><td>数据库编号:</td><td>${project.dbId || 'N/A'}</td></tr>
                            <tr><td>数据库链接:</td><td>${project.dbLink ? '<a href="' + project.dbLink + '" target="_blank">' + project.dbLink + '</a>' : 'N/A'}</td></tr>
                            <tr><td>作者:</td><td>${project.authors || 'N/A'}</td></tr>
                            <tr><td>期刊:</td><td>${project.journal || 'N/A'}</td></tr>
                            <tr><td>创建日期:</td><td>${project.createdDate}</td></tr>
                            <tr><td>项目路径:</td><td><code>${project.path}</code></td></tr>
                        </table>
                        
                        <h6>项目描述</h6>
                        <p>${project.description || '暂无描述'}</p>
                        
                        <h6>标签</h6>
                        <div>
                            ${project.tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <h6>文件列表</h6>
                        <div class="list-group">
                            ${project.files.length > 0 ? project.files.map(file => `
                                <div class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-file-earmark me-2"></i>
                                            ${file.name}
                                        </div>
                                        <small class="text-muted">${file.size}</small>
                                    </div>
                                </div>
                            `).join('') : '<p class="text-muted">暂无文件</p>'}
                        </div>
                    </div>
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('projectDetailModal'));
            modal.show();
        });
}

async function editProject(projectId) {
    console.log('DEBUG: editProject called with projectId:', projectId);
    const project = projects.find(p => p.id === projectId);
    console.log('DEBUG: Found project:', project);
    console.log('DEBUG: project.organism:', project?.organism);
    
    if (!project) return;

    // 更改模态框标题和按钮为编辑模式
    const modalTitle = document.querySelector('#createProjectModal .modal-title');
    const submitButton = document.querySelector('#createProjectModal .modal-footer .btn-primary');

    if (!modalTitle || !submitButton) {
        console.error('无法找到模态框元素');
        showAlert('无法打开编辑界面，请刷新页面重试', 'danger');
        return;
    }

    modalTitle.textContent = '编辑项目';
    submitButton.textContent = '更新项目';
    submitButton.onclick = function() { updateProject(projectId); };

    // 准备表单数据
    const formData = {
        title: project.title,
        doi: project.doi || '',
        dbId: project.dbId || '',
        dbLink: project.dbLink || '',
        dataType: project.dataType,
        data_type: project.dataType,  // 添加 data_type 字段以确保在元数据配置中正确显示
        organism: project.organism,
        authors: project.authors || '',
        journal: project.journal || '',
        description: project.description || '',
        tags: Array.isArray(project.tags) ? project.tags.join(', ') : (project.tags || '')
    };

    // 转换数据类型格式以匹配多选框选项
    // 将逗号分隔的类型转换为与选项匹配的格式
    if (formData.dataType && formData.dataType.includes(',')) {
        const types = formData.dataType.split(',').map(t => t.trim());
        formData.data_type = types.join(',');  // 保持逗号分隔格式
    }

    // 渲染动态表单
    const formContainer = document.getElementById('metadata-form-container');
    await metadataFormRenderer.renderForm(formContainer, formData);

    // 显示创建项目模态框
    const modalElement = document.getElementById('createProjectModal');
    if (!modalElement) {
        console.error('无法找到模态框元素');
        showAlert('无法打开编辑界面，请刷新页面重试', 'danger');
        return;
    }

    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // 当模态框关闭时，恢复为创建模式
    modalElement.addEventListener('hidden.bs.modal', function() {
        modalTitle.textContent = '创建新项目';
        submitButton.textContent = '创建项目';
        submitButton.onclick = function() { createProject(); };
        // 重新渲染空表单
        const formContainer = document.getElementById('metadata-form-container');
        metadataFormRenderer.renderForm(formContainer, {});
    }, { once: true });
}

async function updateProject(projectId) {
    // 从动态表单收集数据
    const formContainer = document.getElementById('metadata-form-container');
    const formData = metadataFormRenderer.collectFormData(formContainer);

    // 验证表单
    const validation = metadataFormRenderer.validateForm(formContainer);
    if (!validation.valid) {
        showAlert('表单验证失败: ' + validation.errors.join(', '), 'danger');
        return;
    }

    // 保存项目到后端
    try {
        console.log('DEBUG: updateProject 发送的数据:', formData);
        const response = await fetch(`/api/update-project/${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // 检查是否成功
        if (!result.success) {
            throw new Error(result.message || '更新失败');
        }

        // 关闭模态框（先移除焦点以避免 aria-hidden 警告）
        const modalElement = document.getElementById('createProjectModal');
        const activeElement = document.activeElement;
        if (activeElement && modalElement.contains(activeElement)) {
            activeElement.blur();
        }
        const modal = bootstrap.Modal.getInstance(modalElement);
        modal.hide();

        // 重置表单
        metadataFormRenderer.renderForm(formContainer, {});

        // 刷新项目列表
        await loadProjects();

        // 刷新显示
        loadProjectsTable();
        updateDashboard();

        // 如果项目详情模态框正在显示，刷新它
        if (selectedProject && selectedProject.id === projectId) {
            showProjectDetail(projectId);
        }

        showAlert('项目更新成功', 'success');
    } catch (error) {
        console.error('更新项目失败:', error);
        showAlert('更新项目失败: ' + error.message, 'danger');
    }
}

async function deleteProject(projectId) {
    if (!confirm('确定要删除这个项目吗？此操作不可撤销。')) {
        return;
    }

    try {
        const response = await fetch(`/api/delete-project/${projectId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.success) {
            // 从本地数组中移除
            const index = projects.findIndex(p => p.id === projectId);
            if (index > -1) {
                projects.splice(index, 1);
                saveProjects();
            }

            // 关闭项目详情模态框（如果打开）
            const detailModalElement = document.getElementById('projectDetailModal');
            if (detailModalElement) {
                const activeElement = document.activeElement;
                if (activeElement && detailModalElement.contains(activeElement)) {
                    activeElement.blur();
                }
                const detailModal = bootstrap.Modal.getInstance(detailModalElement);
                if (detailModal) {
                    detailModal.hide();
                }
            }

            showAlert('项目已删除', 'success');
            loadProjectsTable();
            updateDashboard();
        } else {
            showAlert('删除失败', 'danger');
        }
    } catch (error) {
        console.error('删除项目失败:', error);
        showAlert('删除项目失败: ' + error.message, 'danger');
    }
}

// 浏览数据功能
function loadBrowseData() {
    const projectTree = document.getElementById('project-tree');

    // 从API获取项目列表
    fetch('/api/projects')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(projectList => {
            if (projectList.length === 0) {
                projectTree.innerHTML = '<p class="text-muted p-3">暂无项目</p>';
                return;
            }

            // 按数据类型分组
            const groupedProjects = {};
            projectList.forEach(project => {
                if (!groupedProjects[project.dataType]) {
                    groupedProjects[project.dataType] = [];
                }
                groupedProjects[project.dataType].push(project);
            });

            projectTree.innerHTML = Object.keys(groupedProjects).map(dataType => `
                <div class="tree-item" onclick="toggleDataType('${dataType}')">
                    <i class="bi bi-folder-fill me-2"></i>
                    ${getDataTypeLabel(dataType)} (${groupedProjects[dataType].length})
                </div>
                <div class="tree-children" id="tree-${dataType}">
                    ${groupedProjects[dataType].map(project => `
                        <div class="tree-item" onclick="selectProject('${project.id}')">
                            <i class="bi bi-file-earmark me-2"></i>
                            ${project.title}
                        </div>
                    `).join('')}
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('加载项目列表失败:', error);
            projectTree.innerHTML = `<div class="alert alert-danger m-3">加载项目列表失败: ${error.message}</div>`;
        });
}

function toggleDataType(dataType) {
    const children = document.getElementById(`tree-${dataType}`);
    if (children.style.display === 'none') {
        children.style.display = 'block';
    } else {
        children.style.display = 'none';
    }
}

function selectProject(projectId) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"></div> 加载中...</div>';

    // 先获取项目详情
    fetch(`/api/project/${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(project => {
            // 使用通用扫描端点递归扫描项目目录
            const projectPath = project.path || `/bioraw/data/${projectId}`;
            
            return fetch(`/api/scan-directory?path=${encodeURIComponent(projectPath)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(files => {
                    // 合并项目信息和文件列表
                    project.files = Array.isArray(files) ? files : [];
                    return project;
                });
        })
        .then(project => {
            fileList.innerHTML = `
                <h5>${project.title}</h5>
                <div class="mb-3">
                    <span class="badge data-type-badge" data-type="${project.data_type}">${getDataTypeLabel(project.data_type)}</span>
                    <span class="badge bg-secondary">${project.id}</span>
                </div>

                <h6>文件列表 (${project.files.length} 个文件)</h6>
                ${project.files.length > 0 ? `
                    <div class="list-group">
                        ${project.files.map(file => `
                            <div class="file-item">
                                <div class="file-icon">
                                    <i class="bi bi-file-earmark"></i>
                                </div>
                                <div class="file-info">
                                    <div class="file-name">${file.name}</div>
                                    <div class="file-path text-muted small">${file.path}</div>
                                    <div class="file-size">${file.size}</div>
                                </div>
                                <div class="file-actions">
                                    <button class="btn btn-sm btn-outline-primary" title="下载（功能待实现）">
                                        <i class="bi bi-download"></i>
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p class="text-muted">暂无文件</p>'}
            `;
        })
        .catch(error => {
            console.error('加载项目详情失败:', error);
            fileList.innerHTML = `<div class="alert alert-danger">加载项目详情失败: ${error.message}</div>`;
        });
}

// 目录树功能
function loadDirectoryTree() {
    const content = document.getElementById('directory-tree-content');
    content.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"></div> 加载中...</div>';

    // 从API获取项目列表
    fetch('/api/projects')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(projectList => {
            // 生成目录树
            let tree = '# 生物信息学数据目录结构\n\n';
            tree += '\n';
            tree += '/bioraw/data/\n';

            // 按数据类型分组
            const groupedProjects = {};
            projectList.forEach(project => {
                if (!groupedProjects[project.data_type]) {
                    groupedProjects[project.data_type] = [];
                }
                groupedProjects[project.data_type].push(project);
            });

            Object.keys(groupedProjects).sort().forEach(dataType => {
        tree += `├── ${getDataTypeLabel(dataType)}/\n`;
        const typeProjects = groupedProjects[dataType];
        
        typeProjects.forEach((project, index) => {
            const isLast = index === typeProjects.length - 1;
            const prefix = isLast ? '└──' : '├──';
            tree += `${prefix} ${project.id}_${sanitizeFileName(project.title)}/\n`;
            
            // 添加文件
            if (project.files.length > 0) {
                const filePrefix = isLast ? '    ' : '│   ';
                project.files.forEach((file, fileIndex) => {
                    const isFileLast = fileIndex === project.files.length - 1;
                    const filePrefix2 = isFileLast ? '└──' : '├──';
                    tree += `${filePrefix}${filePrefix2} ${file.name}\n`;
                });
            }
        });
    });
    
    tree += '```\n\n';
    
    // 添加项目统计
    tree += '## 项目统计\n\n';
    tree += `总项目数: ${projects.length}\n\n`;
    
    tree += '### 按数据类型分类\n\n';
    Object.keys(groupedProjects).forEach(dataType => {
        tree += `- **${getDataTypeLabel(dataType)}**: ${groupedProjects[dataType].length} 个项目\n`;
    });
    
    tree += '\n### 按物种分类\n\n';
    const organismCounts = {};
    projects.forEach(project => {
        organismCounts[project.organism] = (organismCounts[project.organism] || 0) + 1;
    });
    Object.keys(organismCounts).forEach(organism => {
        tree += `- **${getOrganismLabel(organism)}**: ${organismCounts[organism]} 个项目\n`;
    });
    
    tree += '\n---\n';
    tree += `*生成时间: ${new Date().toLocaleString()}*\n`;
    
    content.innerHTML = `<pre class="directory-tree">${tree}</pre>`;
        })
        .catch(error => {
            console.error("加载目录树失败:", error);
            content.innerHTML = `<div class="alert alert-danger">加载目录树失败: ${error.message}</div>`;
        });
}

function exportDirectoryTree() {
    const content = document.querySelector('.directory-tree').textContent;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `directory_tree_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showAlert('目录树已导出', 'success');
}

// 工具函数
function setupForms() {
    // 创建项目表单
    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createProject();
        });
    }
    
    // 全局搜索
    const searchForm = document.querySelector('form.d-flex');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('globalSearch').value;
            performGlobalSearch(query);
        });
    }
}

function setupSearch() {
    const searchInput = document.getElementById('globalSearch');
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = this.value.toLowerCase();
            if (query.length > 2) {
                performGlobalSearch(query);
            }
        }, 300);
    });
}

function performGlobalSearch(query) {
    const results = projects.filter(project => 
        project.title.toLowerCase().includes(query) ||
        project.description.toLowerCase().includes(query) ||
        project.tags.some(tag => tag.toLowerCase().includes(query)) ||
        (project.doi && project.doi.toLowerCase().includes(query)) ||
        (project.dbId && project.dbId.toLowerCase().includes(query))
    );
    
    // 显示搜索结果（可以创建一个新的搜索结果页面或模态框）
    console.log('Search results:', results);
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 自动关闭
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

async function showCreateProjectModal() {
    try {
        // 检查元素是否存在
        const modalElement = document.getElementById('createProjectModal');
        const formContainer = document.getElementById('metadata-form-container');
        
        if (!modalElement) {
            console.error('找不到createProjectModal元素');
            showAlert('无法打开创建项目界面', 'danger');
            return;
        }
        
        if (!formContainer) {
            console.error('找不到metadata-form-container元素');
            showAlert('无法加载表单', 'danger');
            return;
        }
        
        // 渲染空的动态表单
        await metadataFormRenderer.renderForm(formContainer, {});

        // 显示模态框
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } catch (error) {
        console.error('显示创建项目模态框失败:', error);
        showAlert('打开创建项目界面失败: ' + error.message, 'danger');
    }
}

function applyProjectFilters() {
    // 实现项目筛选逻辑
    const typeFilter = document.getElementById('project-filter-type').value;
    const organismFilter = document.getElementById('project-filter-organism').value;
    const searchFilter = document.getElementById('project-filter-search').value.toLowerCase();
    
    let filteredProjects = projects;
    
    if (typeFilter) {
        filteredProjects = filteredProjects.filter(p => p.dataType === typeFilter);
    }
    
    if (organismFilter) {
        filteredProjects = filteredProjects.filter(p => p.organism === organismFilter);
    }
    
    if (searchFilter) {
        filteredProjects = filteredProjects.filter(p => 
            p.title.toLowerCase().includes(searchFilter) ||
            p.description.toLowerCase().includes(searchFilter) ||
            p.tags.some(tag => tag.toLowerCase().includes(searchFilter))
        );
    }
    
    // 更新表格显示
    const tbody = document.getElementById('projects-table-body');
    if (filteredProjects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">没有找到匹配的项目</td></tr>';
        return;
    }
    
    tbody.innerHTML = filteredProjects.map(project => `
        <tr>
            <td><span class="badge bg-primary">${project.id}</span></td>
            <td>
                <a href="#" onclick="showProjectDetail('${project.id}')" class="text-decoration-none">
                    ${project.title}
                </a>
            </td>
            <td><span class="badge data-type-badge" data-type="${project.dataType}">${getDataTypeLabel(project.dataType)}</span></td>
            <td>
                <small>
                    ${project.doi ? `DOI: ${project.doi}<br>` : ''}
                    ${project.dbId ? `${project.dbId}` : ''}
                </small>
            </td>
            <td>${getOrganismLabel(project.organism)}</td>
            <td>${project.createdDate}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="showProjectDetail('${project.id}')" title="查看详情">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary" onclick="editProject('${project.id}')" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProject('${project.id}')" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function applyBrowseFilters() {
    // 实现浏览筛选逻辑（类似于项目筛选）
    loadBrowseData();
}

function refreshRecentProjects() {
    updateRecentProjects();
    showAlert('最近项目已刷新', 'success');
}

function refreshDirectoryTree() {
    loadDirectoryTree();
    showAlert('目录树已刷新', 'success');
}

function confirmAdvancedImport() {
    const projectMode = document.querySelector('input[name="projectMode"]:checked').value;
    const selectedFiles = getSelectedFiles();
    
    if (selectedFiles.length === 0) {
        showAlert('请至少选择一个文件进行导入', 'warning');
        return;
    }
    
    let projectData;
    let metadataContainer;
    
    if (projectMode === 'new') {
        // 新建项目
        metadataContainer = document.getElementById('new-project-metadata-fields');
        const renderer = new MetadataFormRenderer();
        const metadata = renderer.collectFormData(metadataContainer);
        
        const descElement = document.getElementById('import-description');
        projectData = {
            id: document.getElementById('import-project-id').value,
            name: document.getElementById('import-project-name').value,
            description: descElement ? descElement.value : '',
            mode: 'new',
            ...metadata
        };

        if (!projectData.name.trim()) {
            showAlert('请填写项目名称', 'warning');
            return;
        }
    } else {
        // 选择已有项目
        const projectId = document.getElementById('select-existing-project').value;
        if (!projectId) {
            showAlert('请选择一个项目', 'warning');
            return;
        }

        metadataContainer = document.getElementById('existing-project-metadata-fields');
        const renderer = new MetadataFormRenderer();
        const metadata = renderer.collectFormData(metadataContainer);

        const projectNameElement = document.getElementById('import-project-name');
        const descElement = document.getElementById('import-description');

        projectData = {
            id: projectId,
            name: projectNameElement ? projectNameElement.value : '',
            description: descElement ? descElement.value : '',
            mode: 'existing',
            ...metadata
        };
    }
    
    const deleteAfterImport = document.getElementById('delete-after-import').checked;
    
    // 禁用按钮并显示进度
    const importButton = document.querySelector('#importProjectModal .modal-footer .btn-primary');
    const originalButtonText = importButton.innerHTML;
    importButton.disabled = true;
    importButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>导入中...';
    
    // 显示进度提示
    const progressAlert = document.createElement('div');
    progressAlert.className = 'alert alert-info mt-3';
    progressAlert.id = 'import-progress';
    progressAlert.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
            <span>正在导入 ${selectedFiles.length} 个文件，请稍候...</span>
        </div>
    `;
    const modalBody = document.querySelector('#importProjectModal .modal-body');
    modalBody.appendChild(progressAlert);
    
    // 发送导入请求
    const importData = {
        project: projectData,
        files: selectedFiles,
        delete_after_import: deleteAfterImport
    };
    
    fetch('/api/advanced-import', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(importData)
    })
    .then(response => response.json())
    .then(data => {
        // 移除进度提示
        const progressElement = document.getElementById('import-progress');
        if (progressElement) {
            progressElement.remove();
        }
        
        // 恢复按钮状态
        importButton.disabled = false;
        importButton.innerHTML = originalButtonText;
        
        if (data.success) {
            showAlert(data.message, 'success');
            const modalElement = document.getElementById('importProjectModal');
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();
            scanDownloadDirectory();
            loadProjects();
            if (currentSection === 'projects') {
                loadProjectsTable();
            }
            updateDashboard();
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('导入失败:', error);
        showAlert('导入失败，请重试', 'danger');
    });
}

function getSelectedFiles() {
    const checkboxes = document.querySelectorAll('#import-file-list input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.value);
}

function loadProjectData(projectId) {
    fetch(`/api/project/${projectId}`)
        .then(response => response.json())
        .then(project => {
            const projectIdElement = document.getElementById('import-project-id');
            const projectNameElement = document.getElementById('import-project-name');
            const descElement = document.getElementById('import-description');
            
            if (projectIdElement) projectIdElement.value = project.id;
            if (projectNameElement) projectNameElement.value = project.name;
            if (descElement) descElement.value = project.description || '';
        })
        .catch(error => {
            console.error('加载项目数据失败:', error);
            showAlert('加载项目数据失败', 'danger');
        });
}

async function resetForm() {
    const formContainer = document.getElementById('metadata-form-container');
    await metadataFormRenderer.renderForm(formContainer, {});
}

// 添加数据到现有项目相关函数
let selectedProjectForData = null;
let selectedDownloadFolder = null;

function showAddDataToProjectModal() {
    const modal = new bootstrap.Modal(document.getElementById('addDataToProjectModal'));
    
    // 加载项目列表
    loadProjectSelectionList();
    
    // 扫描下载目录
    scanDownloadDirectoryForProject();
    
    modal.show();
}

function loadProjectSelectionList() {
    const select = document.getElementById('add-data-project-select');
    
    // 设置加载状态
    select.innerHTML = '<option value="">正在加载项目...</option>';
    select.disabled = true;
    
    // 设置超时处理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
        select.innerHTML = '<option value="">加载超时，请重试</option>';
        select.disabled = false;
        showAlert('加载项目列表超时，请刷新页面重试', 'warning');
    }, 15000); // 15秒超时
    
    fetch('/api/projects', {
        signal: controller.signal,
        timeout: 20000
    })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(projects => {
            select.innerHTML = '<option value="">选择项目...</option>';
            if (projects.length === 0) {
                select.innerHTML += '<option value="" disabled>暂无项目，请先创建项目</option>';
            } else {
                projects.forEach(project => {
                    select.innerHTML += `<option value="${project.id}">${project.title} (${project.id})</option>`;
                });
            }
            select.disabled = false;
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('加载项目列表失败:', error);
            let errorMessage = '加载项目列表失败';
            if (error.name === 'AbortError') {
                errorMessage = '加载项目列表超时，请刷新页面重试';
            } else if (error.message) {
                errorMessage = '加载项目列表失败: ' + error.message;
            }
            select.innerHTML = '<option value="">加载失败，请重试</option>';
            select.disabled = false;
            showAlert(errorMessage, 'warning');
        });
}

function selectProjectForData(projectId) {
    // 取消之前的选择
    document.querySelectorAll('.project-item').forEach(item => {
        item.classList.remove('bg-light', 'border-primary');
    });
    
    // 选择当前项目
    const selectedItem = document.getElementById(`project-item-${projectId}`);
    selectedItem.classList.add('bg-light', 'border-primary');
    
    // 选中对应的radio按钮
    document.getElementById(`project-radio-${projectId}`).checked = true;
    
    selectedProjectForData = projectId;
}

function scanDownloadDirectoryForProject() {
    const resultsDiv = document.getElementById('download-scan-results-for-project');
    resultsDiv.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> 正在扫描下载目录...</div>';
    
    fetch('/api/scan-downloads')
        .then(response => response.json())
        .then(results => {
            displayScanResultsForProject(results);
        })
        .catch(error => {
            console.error('扫描下载目录失败:', error);
            resultsDiv.innerHTML = '<div class="alert alert-danger">扫描下载目录失败: ' + error.message + '</div>';
        });
}

function displayScanResultsForProject(results) {
    const resultsDiv = document.getElementById('download-scan-results-for-project');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">没有发现待处理的下载文件夹</div>';
        return;
    }
    
    resultsDiv.innerHTML = results.map(result => `
        <div class="card mb-2">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${result.name}</h6>
                        <small class="text-muted">
                            ${result.size} | ${result.files} 个文件
                            ${result.detectedDOI ? ` | DOI: ${result.detectedDOI}` : ''}
                            ${result.detectedDbId ? ` | ${result.detectedDbId}` : ''}
                        </small>
                        ${result.detectedType ? `<br><small class="badge bg-info">${getDataTypeLabel(result.detectedType)}</small>` : ''}
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="selectedDownloadFolder" 
                               value="${result.name}" id="folder-${result.name.replace(/[^a-zA-Z0-9]/g, '_')}"
                               onchange="selectDownloadFolderForProject('${result.name}')">
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function selectDownloadFolderForProject(folderName) {
    selectedDownloadFolder = folderName;
}

function confirmAddDataToProject() {
    if (!selectedProjectForData) {
        showAlert('请选择目标项目', 'warning');
        return;
    }
    
    if (!selectedDownloadFolder) {
        showAlert('请选择要添加的下载文件夹', 'warning');
        return;
    }
    
    // 确认对话框
    if (!confirm(`确定要将 "${selectedDownloadFolder}" 中的数据添加到项目 ${selectedProjectForData} 吗？`)) {
        return;
    }
    
    // 发送请求
    fetch('/api/add-data-to-project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            projectId: selectedProjectForData,
            downloadFolder: selectedDownloadFolder
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert(`成功添加 ${result.movedFiles} 个文件到项目 "${result.targetProject}"`, 'success');

            // 关闭模态框（先移除焦点以避免 aria-hidden 警告）
            const modalElement = document.getElementById('addDataToProjectModal');
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();
            
            // 刷新项目列表和仪表板
            loadProjects();
            updateDashboard();
            
            // 重新扫描下载目录
            scanDownloadDirectory();
            
        } else {
            showAlert('添加数据失败: ' + result.error, 'danger');
        }
    })
    .catch(error => {
        console.error('添加数据失败:', error);
        showAlert('添加数据失败: ' + error.message, 'danger');
    });
}

// ==================== 处理数据管理功能 ====================

// 加载处理数据列表
function loadProcessedData() {
    const projectId = document.getElementById('processed-project-filter').value;
    const analysisType = document.getElementById('processed-type-filter').value;
    
    let url = '/api/processed-data';
    if (projectId) {
        url += '?project_id=' + projectId;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayProcessedData(data);
        })
        .catch(error => {
            console.error('加载处理数据失败:', error);
            showAlert('加载处理数据失败: ' + error.message, 'danger');
        });
}

// 显示处理数据列表
function displayProcessedData(processedData) {
    const tbody = document.getElementById('processed-data-table-body');
    tbody.innerHTML = '';
    
    if (processedData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无处理数据</td></tr>';
        return;
    }
    
    processedData.forEach(data => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${data.id}</code></td>
            <td>${data.title}</td>
            <td>${data.project_id || '-'}</td>
            <td><span class="badge bg-info">${getAnalysisTypeLabel(data.analysis_type)}</span></td>
            <td>${data.created_date}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewProcessedData('${data.id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteProcessedData('${data.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 获取分析类型标签
function getAnalysisTypeLabel(type) {
    const labels = {
        'transcriptomics': '转录组分析',
        'scrna-seq': '单细胞分析',
        'spatial': '空间转录组分析',
        'proteomics': '蛋白组分析',
        'differential': '差异分析',
        'pathway': '通路分析',
        'visualization': '可视化',
        'other': '其他'
    };
    return labels[type] || '其他';
}

// 扫描分析目录
function scanAnalysisDirectory() {
    const resultsDiv = document.getElementById('analysis-scan-results');
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> 扫描中...</div>';
    
    fetch('/api/scan-analysis')
        .then(response => response.json())
        .then(data => {
            displayAnalysisResults(data);
        })
        .catch(error => {
            console.error('扫描分析目录失败:', error);
            resultsDiv.innerHTML = '<div class="alert alert-danger">扫描失败: ' + error.message + '</div>';
        });
}

// 显示分析扫描结果
function displayAnalysisResults(results) {
    const resultsDiv = document.getElementById('analysis-scan-results');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">未发现待导入的分析数据文件夹</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    results.forEach(result => {
        html += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${result.info.title || result.folder_name}</h6>
                    <small>${result.files.length} 个文件</small>
                </div>
                <p class="mb-1">${result.info.description || '无描述'}</p>
                <div class="row text-muted small">
                    <div class="col-md-3"><strong>项目ID:</strong> ${result.info.project_id || '未指定'}</div>
                    <div class="col-md-3"><strong>分析类型:</strong> ${getAnalysisTypeLabel(result.info.analysis_type)}</div>
                    <div class="col-md-3"><strong>软件:</strong> ${result.info.software || '未指定'}</div>
                    <div class="col-md-3"><strong>日期:</strong> ${result.info.created_date || '未指定'}</div>
                </div>
                <div class="mt-2">
                    <button class="btn btn-sm btn-primary" onclick="importAnalysisData('${result.folder_path}', '${result.info.project_id || ''}')">
                        <i class="bi bi-upload"></i> 导入
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="viewAnalysisFiles('${result.folder_path}')">
                        <i class="bi bi-folder"></i> 查看文件
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
}

// 导入分析数据
function importAnalysisData(folderPath, projectId) {
    if (!confirm('确定要导入这个分析数据吗？')) {
        return;
    }
    
    const data = {
        folder_path: folderPath,
        project_id: projectId
    };
    
    fetch('/api/import-analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('导入成功: ' + result.message, 'success');
            // 重新扫描分析目录
            scanAnalysisDirectory();
            // 刷新处理数据列表
            loadProcessedData();
        } else {
            showAlert('导入失败: ' + result.message, 'danger');
        }
    })
    .catch(error => {
        console.error('导入失败:', error);
        showAlert('导入失败: ' + error.message, 'danger');
    });
}

// 导入处理数据文件
function importProcessedFile() {
    const filePath = document.getElementById('file-path').value;
    const title = document.getElementById('file-title').value;
    const projectId = document.getElementById('file-project').value;
    const analysisType = document.getElementById('file-analysis-type').value;
    
    if (!filePath) {
        showAlert('请输入文件路径', 'warning');
        return;
    }
    
    const data = {
        file_path: filePath,
        title: title,
        project_id: projectId,
        analysis_type: analysisType
    };
    
    fetch('/api/import-processed-file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('导入成功: ' + result.message, 'success');
            // 清空表单
            document.getElementById('file-import-form').reset();
            // 刷新处理数据列表
            loadProcessedData();
        } else {
            showAlert('导入失败: ' + result.message, 'danger');
        }
    })
    .catch(error => {
        console.error('导入失败:', error);
        showAlert('导入失败: ' + error.message, 'danger');
    });
}

// 查看处理数据详情
function viewProcessedData(processedDataId) {
    fetch(`/api/processed-data/${processedDataId}`)
        .then(response => response.json())
        .then(data => {
            // 创建模态框显示详情
            const modalHtml = `
                <div class="modal fade" id="processedDataModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">处理数据详情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>ID:</strong> <code>${data.id}</code></p>
                                        <p><strong>标题:</strong> ${data.title}</p>
                                        <p><strong>项目ID:</strong> ${data.project_id || '-'}</p>
                                        <p><strong>分析类型:</strong> ${getAnalysisTypeLabel(data.analysis_type)}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>软件:</strong> ${data.software || '-'}</p>
                                        <p><strong>参数:</strong> ${data.parameters || '-'}</p>
                                        <p><strong>创建日期:</strong> ${data.created_date}</p>
                                        <p><strong>路径:</strong> <code>${data.path}</code></p>
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <h6>描述:</h6>
                                    <p>${data.description || '无描述'}</p>
                                </div>
                                <div class="mt-3">
                                    <h6>文件列表:</h6>
                                    <ul class="list-group">
                                        ${data.files.map(file => `
                                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                                <div>
                                                    <i class="bi bi-file-earmark"></i> ${file.name}
                                                    <span class="text-muted small">(${file.size})</span>
                                                </div>
                                                <span class="badge bg-secondary">${file.type}</span>
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有模态框
            const existingModal = document.getElementById('processedDataModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('processedDataModal'));
            modal.show();
        })
        .catch(error => {
            console.error('获取处理数据详情失败:', error);
            showAlert('获取详情失败: ' + error.message, 'danger');
        });
}

// 删除处理数据
function deleteProcessedData(processedDataId) {
    if (!confirm('确定要删除这个处理数据吗？此操作不可撤销！')) {
        return;
    }
    
    fetch(`/api/delete-processed-data/${processedDataId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('删除成功: ' + result.message, 'success');
            // 刷新处理数据列表
            loadProcessedData();
        } else {
            showAlert('删除失败: ' + result.message, 'danger');
        }
    })
    .catch(error => {
        console.error('删除失败:', error);
        showAlert('删除失败: ' + error.message, 'danger');
    });
}

// 查看分析文件（占位函数）
function viewAnalysisFiles(folderPath) {
    showAlert('文件查看功能待实现', 'info');
}

// 更新项目选择器
function updateProjectSelectors() {
    const selectors = [
        'processed-project-filter',
        'file-project'
    ];
    
    selectors.forEach(selectorId => {
        const select = document.getElementById(selectorId);
        if (select) {
            // 保存当前选择
            const currentValue = select.value;
            
            // 清空选项
            select.innerHTML = '<option value="">选择项目（可选）</option>';
            
            // 添加项目选项
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = `${project.id} - ${project.title}`;
                select.appendChild(option);
            });
            
            // 恢复选择
            if (currentValue) {
                select.value = currentValue;
            }
        }
    });
}

// 修复模态框可访问性问题
function setupModalAccessibility() {
    // 监听所有模态框的隐藏事件
    document.addEventListener('hide.bs.modal', function(event) {
        const modal = event.target;
        
        // 移除模态框上任何元素的焦点
        if (modal.contains(document.activeElement)) {
            document.activeElement.blur();
        }
        
        // 确保焦点不会停留在模态框内的任何元素上
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        focusableElements.forEach(element => {
            if (document.activeElement === element) {
                element.blur();
            }
        });
    });
    
    // 监听所有模态框的显示事件
    document.addEventListener('shown.bs.modal', function(event) {
        const modal = event.target;

        // 将焦点设置到模态框的第一个可聚焦元素
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        } else {
            // 如果没有可聚焦元素，将焦点设置到模态框本身
            modal.setAttribute('tabindex', '-1');
            modal.focus();
        }
    });

    // 监听所有模态框的隐藏前事件
    document.addEventListener('hidePrevented.bs.modal', function(event) {
        // 隐藏被阻止时无需额外处理
    });
    
    // 为ESC键添加特殊处理
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                // 在关闭模态框前移除焦点
                if (openModal.contains(document.activeElement)) {
                    document.activeElement.blur();
                }
            }
        }
    });
}