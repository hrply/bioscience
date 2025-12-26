# Docker镜像优化建议

## 当前大小：419MB（合理范围）

## 进一步优化方案

### 1. 使用Alpine基础镜像（可减少~100MB）
```dockerfile
FROM python:3.10-alpine AS builder
# 注意：需要处理Alpine的兼容性问题
```

### 2. 多阶段构建优化（可减少~50MB）
```dockerfile
# 在builder阶段只安装必要的构建依赖
# 在production阶段只安装运行时依赖
```

### 3. 减少Python包
- 检查requirements.txt中是否有未使用的包
- 使用更小的替代包（如用h5py替代pytables）

### 4. 字体优化（可减少~20MB）
- 只安装必要的字体而不是完整字体包
- 使用字体子集

### 5. 清理包管理器缓存
```dockerfile
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

## 当前配置已经是较好的平衡
- 419MB对于包含matplotlib的科学应用是合理的
- 相比其他类似应用（如jupyter镜像通常1GB+）已经很小
- 保持了完整功能和中文支持