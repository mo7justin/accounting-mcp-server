# AI记账MCP工具

基于 Model Context Protocol (MCP) 的个人记账管理工具，为 AI 助手提供财务管理功能，实现"只需要说话就能记账"的便捷体验。

## 功能特性

### MCP Tools（AI 可调用的工具）

- **add_transaction** - 添加收支记录
- **get_balance** - 查询账户余额
- **list_transactions** - 查询交易记录（支持筛选）
- **get_monthly_summary** - 获取月度财务汇总

### MCP Resources（AI 可访问的数据）

- **transactions://all** - 所有交易记录
- **categories://list** - 支出分类列表
- **summary://current** - 账户汇总信息

## 快速开始

### 环境要求

- Python 3.11+
- pip 或 conda

### 安装依赖

```bash
# 使用 pip 安装依赖
pip install -r requirements.txt

# 开发环境依赖（可选）
pip install -r requirements-dev.txt
```

### 运行服务器

```bash
# 直接运行 MCP 服务器
python -m accounting_mcp.server
```

### 使用测试客户端

```bash
# 运行交互式测试客户端
python test_client.py
```

## 使用示例

### 添加交易记录

```bash
# 添加一笔支出
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"add_transaction","params":{"amount":-50,"category":"food","description":"午餐"},"id":1}' http://localhost:8000

# 添加一笔收入
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"add_transaction","params":{"amount":5000,"category":"salary","description":"月薪"},"id":2}' http://localhost:8000
```

### 查询余额

```bash
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"get_balance","params":{},"id":3}' http://localhost:8000
```

### 查看交易记录

```bash
# 查看最近30天的交易
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"list_transactions","params":{"days":30},"id":4}' http://localhost:8000

# 查看特定分类的交易
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"list_transactions","params":{"category":"food"},"id":5}' http://localhost:8000
```

### 查看月度汇总

```bash
# 查看当前月份汇总
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"get_monthly_summary","params":{},"id":6}' http://localhost:8000

# 查看指定月份汇总
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"get_monthly_summary","params":{"year":2024,"month":1},"id":7}' http://localhost:8000
```

## 项目结构

```
accounting_mcp/
├── __init__.py         # 包初始化
├── server.py           # MCP 服务器主程序  
├── models.py           # 数据模型定义
├── storage.py          # JSON 文件存储
└── tools.py            # MCP 工具实现
data/                    # 数据文件目录
tests/                   # 测试代码
requirements.txt        # 项目依赖
requirements-dev.txt    # 开发依赖
test_client.py          # 交互测试客户端
```

## AI 助手集成

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "accounting": {
      "command": "python",
      "args": ["/path/to/accounting_mcp/server.py"],
      "env": {}
    }
  }
}
```

### 使用示例对话

用户: "帮我记录一笔35元的午餐费用"
Claude: 已为您添加35元的餐饮支出，当前余额为1,965元。

用户: "我这个月在食物上花了多少钱？"
Claude: 根据记录，您本月在餐饮分类上总计支出285元。

用户: "我的账户余额是多少？"
Claude: 您当前的账户余额为1,965元。

## 技术架构

- **传输层**: stdio（标准输入输出）
- **协议层**: JSON-RPC 2.0
- **应用层**: 工具注册和资源管理
- **数据存储**: 轻量级 JSON 文件存储

## 开发指南

### 运行测试

```bash
# 运行基本测试
python tests/test_basic.py

# 运行所有测试（使用pytest）
pytest
```

### 代码质量检查

```bash
# 格式化代码
black accounting_mcp/

# 风格检查
flake8 accounting_mcp/
```

## 扩展和定制

### 添加新的分类

编辑 `data/categories.json` 文件，添加自定义的支出分类。

### 添加新的工具

1. 在 `tools.py` 中定义新的工具函数
2. 在 `server.py` 中注册工具
3. 编写对应的测试用例

## 许可证

本项目基于 MIT 许可证开源。