# Docker部署指南

本文档提供了在Docker环境中部署和运行MCP记账服务器的详细步骤。

## 环境要求

- Docker 20.10+ 或 Docker Desktop
- Docker Compose 1.29+

## 快速开始

### 使用Docker Compose（推荐）

Docker Compose提供了最简单的部署方式，自动处理构建和配置：

```bash
# 在项目根目录执行
docker-compose up -d
```

这将：
- 构建Docker镜像
- 创建并启动容器
- 配置端口映射(8000:8000)
- 设置数据持久化卷

### 手动构建Docker镜像

如果您想单独构建镜像并手动运行容器：

```bash
# 构建镜像
docker build -t accounting-mcp-server .

# 运行容器
docker run -d \
  --name accounting-mcp-server \
  -p 8000:8000 \
  -v accounting-mcp-data:/app/data \
  accounting-mcp-server
```

## 配置说明

### 环境变量

您可以通过环境变量自定义服务器配置：

- `STUDIO_HOST`: 服务器监听地址 (默认: 0.0.0.0)
- `STUDIO_PORT`: 服务器监听端口 (默认: 8000)
- `STUDIO_PROTOCOL`: 协议 (http 或 https，默认: http)
- `ENABLE_STUDIO`: 是否启用STUDIO模式 (true/false，默认: true)
- `DATA_DIR`: 数据存储目录 (默认: /app/data)
- `DOCKER_ENV`: 是否运行在Docker环境中 (默认: true)

### 数据持久化

Docker Compose会自动创建命名卷`accounting-mcp-data`用于数据持久化，即使删除并重新创建容器，数据也不会丢失。

您也可以使用主机目录进行挂载：

```bash
# 使用主机目录
mkdir -p ./docker-data

docker run -d \
  --name accounting-mcp-server \
  -p 8000:8000 \
  -v $(pwd)/docker-data:/app/data \
  accounting-mcp-server
```

## 验证服务

启动容器后，可以通过以下方式验证服务是否正常运行：

### 健康检查

```bash
curl http://localhost:8000/health
```

正常响应应该是：
```json
{"status":"healthy","timestamp":"2024-01-01T12:00:00.000000","service":"accounting-mcp-server"}
```

### 测试通信

您可以使用项目提供的测试脚本（在宿主机上运行）：

```bash
python test_studio_communication.py
```

## 管理容器

### 查看日志

```bash
docker logs accounting-mcp-server
# 或使用Docker Compose
docker-compose logs -f
```

### 停止服务

```bash
# 单个容器
docker stop accounting-mcp-server
# 或使用Docker Compose
docker-compose down
```

### 启动服务

```bash
# 单个容器
docker start accounting-mcp-server
# 或使用Docker Compose
docker-compose up -d
```

## 更新服务

当代码有更新时，需要重新构建和启动服务：

```bash
# 使用Docker Compose
docker-compose down
docker-compose build
docker-compose up -d

# 或手动更新
docker stop accounting-mcp-server
docker rm accounting-mcp-server
docker build -t accounting-mcp-server .
docker run -d --name accounting-mcp-server -p 8000:8000 -v accounting-mcp-data:/app/data accounting-mcp-server
```

## 注意事项

1. 数据安全性：请确保备份数据卷中的重要数据
2. 性能优化：对于高负载场景，可以调整容器资源限制
3. 网络配置：如需在生产环境中使用，请配置适当的防火墙和安全策略

## 故障排除

### 容器启动失败

检查日志以获取错误信息：
```bash
docker logs accounting-mcp-server
```

### 端口冲突

如果端口8000已被占用，修改docker-compose.yml中的端口映射或容器的环境变量配置。

### 数据访问问题

检查文件权限，确保容器内用户有权限读写数据目录。