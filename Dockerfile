# 使用Python官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据目录（用于存储JSON数据文件）
RUN mkdir -p data

# 设置环境变量
ENV STUDIO_HOST=0.0.0.0
ENV STUDIO_PORT=8000
ENV ENABLE_STUDIO=true

# 暴露端口
EXPOSE 8000

# 设置默认命令运行STUDIO服务器
CMD ["python", "accounting_mcp/studio_server.py"]