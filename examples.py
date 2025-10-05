"""MCP记账工具使用示例"""

import json
import subprocess
import sys
import time


def send_mcp_request(request):
    """发送MCP请求到服务器并获取响应"""
    # 启动服务器进程
    process = subprocess.Popen(
        [sys.executable, "-m", "accounting_mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 等待服务器启动
        time.sleep(0.5)
        
        # 发送请求
        request_str = json.dumps(request, ensure_ascii=False) + '\n'
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # 读取响应
        response_str = process.stdout.readline()
        if response_str:
            response = json.loads(response_str)
            return response
        else:
            return None
            
    finally:
        # 清理进程
        process.terminate()
        try:
            process.wait(timeout=1)
        except:
            pass


def example_add_transaction():
    """示例：添加交易记录"""
    print("=== 添加交易记录示例 ===")
    
    # 添加一笔支出
    request_expense = {
        "jsonrpc": "2.0",
        "method": "add_transaction",
        "params": {
            "amount": -50,
            "category": "food",
            "description": "午餐"
        },
        "id": 1
    }
    
    response = send_mcp_request(request_expense)
    if response:
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")
    
    # 添加一笔收入
    request_income = {
        "jsonrpc": "2.0",
        "method": "add_transaction",
        "params": {
            "amount": 5000,
            "category": "salary",
            "description": "月薪"
        },
        "id": 2
    }
    
    response = send_mcp_request(request_income)
    if response:
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

def example_get_balance():
    """示例：查询余额"""
    print("\n=== 查询余额示例 ===")
    
    request = {
        "jsonrpc": "2.0",
        "method": "get_balance",
        "params": {},
        "id": 3
    }
    
    response = send_mcp_request(request)
    if response:
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

def example_list_transactions():
    """示例：查询交易记录"""
    print("\n=== 查询交易记录示例 ===")
    
    request = {
        "jsonrpc": "2.0",
        "method": "list_transactions",
        "params": {
            "days": 30
        },
        "id": 4
    }
    
    response = send_mcp_request(request)
    if response:
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

def example_get_monthly_summary():
    """示例：获取月度汇总"""
    print("\n=== 获取月度汇总示例 ===")
    
    request = {
        "jsonrpc": "2.0",
        "method": "get_monthly_summary",
        "params": {},
        "id": 5
    }
    
    response = send_mcp_request(request)
    if response:
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

def example_ai_integration():
    """示例：AI助手集成（模拟）"""
    print("\n=== AI助手集成示例 ===")
    print("用户: 帮我记录一笔35元的午餐费用")
    print("AI: 正在为您记录午餐支出...")
    
    # AI会调用的MCP请求
    request = {
        "jsonrpc": "2.0",
        "method": "add_transaction",
        "params": {
            "amount": -35,
            "category": "food",
            "description": "午餐"
        },
        "id": 6
    }
    
    response = send_mcp_request(request)
    if response and "result" in response:
        result = response["result"]
        print(f"AI: {result['message']}")
    
    print("\n用户: 我这个月花了多少钱？")
    print("AI: 正在查询您的月度支出...")
    
    # 查询月度汇总
    summary_request = {
        "jsonrpc": "2.0",
        "method": "get_monthly_summary",
        "params": {},
        "id": 7
    }
    
    summary_response = send_mcp_request(summary_request)
    if summary_response and "result" in summary_response:
        result = summary_response["result"]
        print(f"AI: {result['message']}")

def main():
    """运行所有示例"""
    print("MCP记账工具使用示例")
    print("=" * 50)
    
    try:
        # 运行各个示例
        example_add_transaction()
        example_get_balance()
        example_list_transactions()
        example_get_monthly_summary()
        example_ai_integration()
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("提示：在实际使用中，您可以将此MCP服务器与Claude等AI助手集成，实现语音记账功能。")
        
    except Exception as e:
        print(f"运行示例时发生错误: {e}")


if __name__ == "__main__":
    main()