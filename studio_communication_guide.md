# 小智AI记账系统 - STUDIO通信配置指南

本文档详细介绍如何配置和使用小智AI记账系统的STUDIO通信模式。

## 两种通信模式

小智AI记账系统支持两种通信模式：

1. **标准IO通信模式**：通过子进程的标准输入输出进行通信（默认模式）
2. **STUDIO HTTP API通信模式**：通过HTTP API进行通信，更适合与STUDIO平台集成

## 配置STUDIO通信

### 1. 配置文件设置

系统使用`config.env`文件进行配置。默认配置如下：

```
# STUDIO服务器配置
STUDIO_HOST=localhost
STUDIO_PORT=8000

# STUDIO API密钥（如果需要）
STUDIO_API_KEY=

# STUDIO通信协议（http或https）
STUDIO_PROTOCOL=http

# 启用STUDIO通信
ENABLE_STUDIO=true

# 客户端使用STUDIO模式
USE_STUDIO=false
```

### 2. 环境变量配置

你也可以通过环境变量覆盖配置文件中的设置：

- `STUDIO_HOST`: STUDIO服务器主机名
- `STUDIO_PORT`: STUDIO服务器端口
- `STUDIO_API_KEY`: STUDIO API密钥
- `STUDIO_PROTOCOL`: STUDIO通信协议（http或https）
- `ENABLE_STUDIO`: 服务器是否启用STUDIO通信（true或false）
- `USE_STUDIO`: 客户端是否使用STUDIO通信模式（true或false）

## 服务器端设置

### 启动支持STUDIO的服务器

有两种方式启动支持STUDIO的服务器：

#### 方式1：使用studio_server.py（同时支持标准IO和STUDIO）

```bash
python accounting_mcp/studio_server.py
```

这种方式启动的服务器同时支持：
- 标准IO通信（通过stdin/stdout）
- STUDIO HTTP API通信（通过配置的端口）

#### 方式2：通过主程序自动启动（推荐）

当运行主程序时，如果检测到studio_server.py，它会自动使用此脚本启动服务器：

```bash
python xiaozhi_voice_integration.py
```

### 服务器端点

启动STUDIO服务器后，可用的端点：

1. **API端点**：`http://[STUDIO_HOST]:[STUDIO_PORT]`
   - 用于发送JSON-RPC请求
   - 请求格式与标准IO模式相同

2. **健康检查端点**：`http://[STUDIO_HOST]:[STUDIO_PORT]/health`
   - 用于检查服务器是否正常运行
   - 返回服务器状态信息

## 客户端设置

### 使用STUDIO模式的客户端

要让客户端使用STUDIO模式，需要：

1. 设置`USE_STUDIO=true`（在config.env文件中）
2. 确保STUDIO服务器已启动并可访问

客户端会自动尝试连接到配置的STUDIO服务器，并发送HTTP请求而不是通过子进程管道通信。

### 示例：配置为使用STUDIO模式

修改`config.env`文件：

```
# 客户端使用STUDIO模式
USE_STUDIO=true

# STUDIO服务器配置
STUDIO_HOST=localhost
STUDIO_PORT=8000
```

然后运行客户端：

```bash
python xiaozhi_voice_integration.py
```

## 安全性

### API密钥保护

如果需要保护STUDIO API，可以配置API密钥：

1. 在服务器和客户端的`config.env`文件中设置相同的`STUDIO_API_KEY`
2. 客户端发送请求时会自动添加认证头
3. 服务器会验证请求中的API密钥

## 故障排除

### 服务器无法启动

- 检查端口是否被占用
- 确认Python依赖已安装：`pip install -r requirements.txt`
- 查看错误日志获取详细信息

### 客户端无法连接到STUDIO服务器

- 确认STUDIO服务器正在运行
- 检查`STUDIO_HOST`和`STUDIO_PORT`配置是否正确
- 验证网络连接和防火墙设置
- 尝试使用健康检查端点测试连接：`http://[STUDIO_HOST]:[STUDIO_PORT]/health`

### API密钥认证失败

- 确保服务器和客户端使用相同的API密钥
- 检查密钥中是否包含特殊字符或空格

## 示例代码

### 直接使用HTTP API

除了使用集成的客户端，你也可以直接通过HTTP API与服务器通信：

```python
import requests
import json

# 服务器地址
url = "http://localhost:8000"

# 请求头
headers = {
    'Content-Type': 'application/json',
    # 如有API密钥，取消下面这行的注释并填入密钥
    # 'Authorization': 'Bearer your_api_key_here'
}

# 构建请求
request = {
    "jsonrpc": "2.0",
    "method": "process_voice_command",
    "params": {"command": "我这个月花了多少钱？"},
    "id": 1
}

# 发送请求
response = requests.post(url, json=request, headers=headers)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print("响应:", result)
else:
    print(f"错误: {response.status_code}")
    print("响应内容:", response.text)
```