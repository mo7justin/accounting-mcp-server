#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小智AI语音记账集成脚本

此模块提供了小智AI语音助手与记账MCP服务的集成功能，支持两种通信模式：
1. 标准输入输出（stdio）通信模式
2. STUDIO HTTP API通信模式

可通过环境变量或配置文件配置通信模式和STUDIO服务器地址
"""

import json
import subprocess
import sys
import time
import re
import os
import requests
from datetime import datetime, date

# 从配置文件加载环境变量
try:
    from dotenv import load_dotenv
    # 加载配置文件
    load_dotenv('config.env')
except ImportError:
    print("警告: dotenv模块未安装，将使用环境变量或默认值")

# 获取配置
USE_STUDIO = os.getenv('USE_STUDIO', 'false').lower() == 'true'
STUDIO_HOST = os.getenv('STUDIO_HOST', 'localhost')
STUDIO_PORT = os.getenv('STUDIO_PORT', '8000')
STUDIO_PROTOCOL = os.getenv('STUDIO_PROTOCOL', 'http')
STUDIO_API_KEY = os.getenv('STUDIO_API_KEY', '')
STUDIO_URL = f"{STUDIO_PROTOCOL}://{STUDIO_HOST}:{STUDIO_PORT}"

def start_mcp_server():
    """启动MCP服务器进程
    
    如果使用STUDIO模式，则不会启动本地进程，而是假设STUDIO服务器已在运行
    
    Returns:
        服务器进程对象，或None表示启动失败或STUDIO模式
    """
    # STUDIO模式下，不启动本地服务器
    if USE_STUDIO:
        print("使用STUDIO模式，不会启动本地MCP服务器进程")
        print(f"STUDIO服务器URL: {STUDIO_URL}")
        
        # 尝试进行健康检查
        try:
            health_url = f"{STUDIO_URL}/health"
            headers = {}
            if STUDIO_API_KEY:
                headers['Authorization'] = f'Bearer {STUDIO_API_KEY}'
            
            response = requests.get(health_url, headers=headers, timeout=5)
            if response.status_code == 200:
                print("STUDIO服务器健康检查成功")
            else:
                print(f"警告: STUDIO服务器健康检查失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"警告: 无法连接到STUDIO服务器: {e}")
            print("请确保STUDIO服务器已启动并且配置正确")
        
        return None
    
    # 标准模式，启动本地服务器
    try:
        # 获取项目根目录路径
        import os
        project_root = os.path.dirname(__file__)
        
        # 设置环境变量，确保Python能找到accounting_mcp模块
        env = os.environ.copy()
        # 将项目根目录添加到PYTHONPATH
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = project_root
        
        # 首先尝试查找studio_server.py
        server_path = os.path.join(project_root, 'accounting_mcp', 'studio_server.py')
        # 如果不存在，回退到server.py
        if not os.path.exists(server_path):
            server_path = os.path.join(project_root, 'accounting_mcp', 'server.py')
        
        # 在Windows上，使用text=True参数处理文本模式，设置bufsize=1启用行缓冲
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # 行缓冲以确保及时通信
            env=env
        )
        
        print("MCP服务器已启动")
        
        # 给服务器一点启动时间
        import time
        time.sleep(2)  # 保留较长的启动时间
        
        # 检查进程是否仍在运行
        if process.poll() is not None:
            print(f"服务器启动失败，退出码: {process.poll()}")
            error = process.stderr.read()
            if error:
                print(f"服务器错误: {error}")
            return None
            
        return process
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_mcp_request(process, method, params=None, request_id=1):
    """向MCP服务器发送请求并获取响应
    
    Args:
        process: MCP服务器进程，STUDIO模式下为None
        method: 调用的方法名
        params: 方法参数
        request_id: 请求ID
        
    Returns:
        响应结果字典，或None表示失败
    """
    # 构建请求
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id
    }
    
    if params:
        # 处理datetime对象的序列化问题
        if isinstance(params, dict):
            for key, value in params.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    params[key] = value.isoformat()
        request["params"] = params
    
    # STUDIO模式，通过HTTP发送请求
    if USE_STUDIO:
        return send_studio_request(request)
    
    # 标准模式，通过进程管道发送请求
    if not process:
        print("服务器进程未启动")
        return None
    
    # 检查进程是否仍在运行
    if process.poll() is not None:
        print(f"服务器进程已终止，退出码: {process.poll()}")
        return None
    
    try:
        # 序列化请求为JSON字符串
        request_str = json.dumps(request, ensure_ascii=False)
        
        print(f"发送请求: {request_str}")  # 添加调试信息
        
        # 尝试发送请求，但捕获可能的错误
        try:
            process.stdin.write(request_str + '\n')
            process.stdin.flush()
        except (OSError, IOError) as e:
            print(f"写入管道时发生错误: {e}")
            # 检查进程状态
            if process.poll() is not None:
                print(f"服务器已终止，退出码: {process.poll()}")
                error = process.stderr.read()
                if error:
                    print(f"服务器错误输出: {error}")
            return None
        
        # 给服务器一点处理时间
        import time
        time.sleep(0.5)
        
        # 尝试读取响应
        try:
            response_str = process.stdout.readline()
            if response_str:
                response_str = response_str.rstrip('\n\r')
                print(f"收到响应: {response_str}")  # 添加调试信息
                try:
                    return json.loads(response_str)
                except json.JSONDecodeError:
                    print(f"响应解析错误: {response_str}")
                    return None
            else:
                # 如果第一次读取为空，再尝试一次
                time.sleep(0.5)
                response_str = process.stdout.readline()
                if response_str:
                    response_str = response_str.rstrip('\n\r')
                    print(f"收到响应: {response_str}")  # 添加调试信息
                    try:
                        return json.loads(response_str)
                    except json.JSONDecodeError:
                        print(f"响应解析错误: {response_str}")
                        return None
                else:
                    print("未收到响应，尝试检查服务器状态")
                    # 尝试读取错误输出
                    error = process.stderr.read(1024)  # 只读取一部分，避免阻塞
                    if error:
                        print(f"服务器可能有错误: {error}")
                    # 检查进程是否还在运行
                    if process.poll() is not None:
                        print(f"服务器已终止，退出码: {process.poll()}")
                    return None
        except (OSError, IOError) as e:
            print(f"读取响应时发生错误: {e}")
            return None
            
    except Exception as e:
        print(f"发送请求时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_studio_request(request):
    """
    通过STUDIO HTTP API发送请求
    
    Args:
        request (dict): 请求对象
        
    Returns:
        dict: 服务器响应
    """
    try:
        print(f"通过STUDIO API发送请求到 {STUDIO_URL}")
        # 设置请求头
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 如果配置了API密钥，添加认证头
        if STUDIO_API_KEY:
            headers['Authorization'] = f'Bearer {STUDIO_API_KEY}'
        
        # 发送POST请求
        response = requests.post(
            STUDIO_URL,
            json=request,
            headers=headers,
            timeout=10
        )
        
        # 检查响应状态码
        if response.status_code == 200:
            result = response.json()
            print(f"STUDIO API响应: {result}")
            return result
        else:
            print(f"STUDIO服务器返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return {"error": {"message": f"服务器返回错误: {response.status_code}"}}
    except requests.exceptions.RequestException as e:
        print(f"STUDIO API请求失败: {e}")
        return {"error": {"message": f"STUDIO通信失败: {str(e)}"}}
    except Exception as e:
        print(f"处理STUDIO响应时出错: {e}")
        return {"error": {"message": f"STUDIO处理失败: {str(e)}"}}

def parse_voice_command(text):
    """解析语音命令"""
    # 转小写处理
    text = text.lower()
    print(f"原始文本: '{text}'")  # 添加调试信息
    
    # 先匹配更具体的模式，后匹配更通用的模式
    
    # 记录支出模式 - 简化版本专门匹配"帮我记录一笔35元的午餐费用"这样的模式
    expense_pattern = re.compile(r'(帮我记录一笔)?(\d+(?:\.\d+)?)元(?:的)?(.+)')
    expense_match = expense_pattern.search(text)
    print(f"支出模式匹配结果: {expense_match}")  # 添加调试信息
    
    if expense_match:
        print(f"支出模式捕获组: {expense_match.groups()}")  # 添加调试信息
        # 解析支出
        amount = float(expense_match.group(2))
        description = expense_match.group(3)
        
        # 自动分类
        category = categorize_expense(description)
        
        return {
            "action": "add_transaction",
            "params": {
                "amount": -amount,  # 负数表示支出
                "category": category,
                "description": description
            }
        }
    
    # 记录收入模式 - 简化版本
    income_pattern = re.compile(r'(帮我记录一笔)?(\d+(?:\.\d+)?)元(?:的)?(.+?)(?:收入|工资|奖金)')
    income_match = income_pattern.search(text)
    print(f"收入模式匹配结果: {income_match}")  # 添加调试信息
    
    if income_match:
        # 解析收入
        amount = float(income_match.group(2))
        description = income_match.group(3)
        
        # 自动分类
        category = categorize_income(description)
        
        return {
            "action": "add_transaction",
            "params": {
                "amount": amount,  # 正数表示收入
                "category": category,
                "description": description
            }
        }
    
    # 查询月度汇总模式
    summary_pattern = re.compile(r'(本月|这个月)(?:花了|支出|花费|收入)(?:多少|总计)')
    summary_match = summary_pattern.search(text)
    
    if summary_match:
        return {
            "action": "get_monthly_summary",
            "params": {}
        }
    
    # 查询交易记录模式
    transaction_pattern = re.compile(r'(最近|今天|昨天)(\d+)?天?(?:的)?(交易|记录|支出|收入)')
    transaction_match = transaction_pattern.search(text)
    
    if transaction_match:
        # 解析天数
        days = transaction_match.group(2)
        days = int(days) if days else 7  # 默认7天
        
        return {
            "action": "list_transactions",
            "params": {"days": days}
        }
    
    # 查询余额模式 - 使其更精确
    balance_pattern = re.compile(r'(账户余额|余额|还有多少钱)')
    balance_match = balance_pattern.search(text)
    
    if balance_match:
        return {
            "action": "get_balance",
            "params": {}
        }
    
    # 如果所有模式都不匹配
    return {
        "action": "unknown",
        "params": {},
        "error": "无法识别的命令，请尝试其他说法"
    }

def categorize_expense(description):
    """根据描述自动分类支出"""
    description = description.lower()
    
    # 食物相关
    food_keywords = ['餐', '饭', '外卖', '餐饮', '午餐', '晚餐', '早餐', '吃', '食']
    for keyword in food_keywords:
        if keyword in description:
            return "food"
    
    # 交通相关
    transport_keywords = ['交通', '地铁', '公交', '打车', '出租车', '地铁卡', '公交卡', '停车', '加油']
    for keyword in transport_keywords:
        if keyword in description:
            return "transport"
    
    # 购物相关
    shopping_keywords = ['买', '购物', '超市', '淘宝', '京东', '服装', '鞋', '化妆品', '电器']
    for keyword in shopping_keywords:
        if keyword in description:
            return "shopping"
    
    # 娱乐相关
    entertainment_keywords = ['电影', '游戏', '娱乐', 'KTV', '聚会', '酒吧', '旅行', '旅游', '景点']
    for keyword in entertainment_keywords:
        if keyword in description:
            return "entertainment"
    
    # 默认分类
    return "shopping"

def categorize_income(description):
    """根据描述自动分类收入"""
    description = description.lower()
    
    if '工资' in description:
        return "salary"
    elif '奖金' in description:
        return "bonus"
    elif '投资' in description or '股票' in description or '理财' in description:
        return "investment"
    else:
        return "salary"

def format_response(response, action):
    """格式化响应结果"""
    if not response or "error" in response:
        error_msg = response["error"]["message"] if response else "未收到响应"
        return f"操作失败: {error_msg}"
    
    result = response.get("result", {})
    
    if action == "add_transaction":
        return result.get("message", "交易已添加")
    elif action == "get_balance":
        return f"您当前的账户余额为{result['balance']:.2f}元"
    elif action == "get_monthly_summary":
        if "summary" in result:
            summary = result["summary"]
            return f"您在{summary['month']}月的支出为{summary['total_expense']:.2f}元，收入为{summary['total_income']:.2f}元，月度结余为{summary['balance_change']:.2f}元"
        else:
            return result.get("message", "未找到月度汇总信息")
    elif action == "list_transactions":
        transactions = result.get("transactions", [])
        if not transactions:
            return "暂无交易记录"
        
        count = len(transactions)
        return f"最近有{count}条交易记录"
    else:
        return result.get("message", "操作完成")

# 删除重复的handle_voice_command函数定义

# 保留原始的handle_voice_command函数定义
def handle_voice_command(process, command_result):
    """处理语音命令解析结果，调用相应的MCP方法"""
    action = command_result.get('action')
    params = command_result.get('params', {})
    
    # 处理不同的命令类型
    if action == 'add_transaction':
        # 添加交易记录
        response = send_mcp_request(process, 'add_transaction', params)
    elif action == 'get_balance':
        # 查询余额
        response = send_mcp_request(process, 'get_balance', params)
    elif action == 'get_monthly_summary':
        # 获取月度汇总
        response = send_mcp_request(process, 'get_monthly_summary', params)
    elif action == 'list_transactions':
        # 列出交易记录
        response = send_mcp_request(process, 'list_transactions', params)
    elif action == 'unknown':
        # 未知命令
        return command_result.get('error', '无法识别的命令')
    else:
        return f'未支持的命令类型: {action}'
    
    # 处理响应
    if not response:
        return '操作失败: 未收到响应'
    
    if 'error' in response:
        return f'操作失败: {response["error"].get("message", "未知错误")}'
    
    result = response.get('result', {})
    
    # 根据不同命令类型格式化响应
    if action == 'add_transaction':
        return result.get('message', '交易记录添加成功')
    elif action == 'get_balance':
        balance = result.get('balance', 0.0)
        return f'您的账户余额为 {balance:.2f} 元'
    elif action == 'get_monthly_summary':
        summary = result.get('summary', {})
        if not summary:
            return '暂无月度数据'
        month = summary.get('month', '')
        income = summary.get('total_income', 0.0)
        expense = summary.get('total_expense', 0.0)
        return f'{month}月收入 {income:.2f} 元，支出 {expense:.2f} 元'
    elif action == 'list_transactions':
        transactions = result.get('transactions', [])
        if not transactions:
            return '暂无交易记录'
        # 简单返回交易数量
        return f'共有 {len(transactions)} 条交易记录'
    
    return '操作完成'

def voice_accounting_demo():
    """语音记账演示模式"""
    # 启动MCP服务器（STUDIO模式下不会启动本地进程）
    mcp_server = start_mcp_server()
    if not USE_STUDIO and not mcp_server:
        return
    
    try:
        print("\n=== 小智AI语音记账系统 ===")
        print(f"当前通信模式: {'STUDIO HTTP API' if USE_STUDIO else '标准IO'}")
        print("请输入您的语音命令（输入'退出'结束）：")
        
        while True:
            # 模拟语音输入（实际使用时，这里应该接入语音识别API）
            voice_input = input("\n语音输入: ").strip()
            
            if voice_input.lower() in ['退出', 'exit', 'quit']:
                break
            
            # 解析语音命令
            parsed = parse_voice_command(voice_input)
            
            if parsed["action"] == "unknown":
                print(f"小智: {parsed['error']}")
                continue
            
            # 发送MCP请求
            response = send_mcp_request(
                mcp_server,
                parsed["action"],
                parsed["params"]
            )
            
            # 格式化并显示响应
            result_text = format_response(response, parsed["action"])
            print(f"小智: {result_text}")
            
    finally:
        # 停止服务器（如果是标准模式）
        if not USE_STUDIO and mcp_server:
            print("\n正在停止MCP服务器...")
            mcp_server.terminate()
            mcp_server.wait(timeout=5)
            print("服务器已停止")

def simulate_xiaozhi_integration():
    """模拟小智AI服务器集成"""
    print("\n=== 模拟小智AI服务器集成演示 ===")
    print("以下是模拟小智AI服务器如何调用MCP记账功能的示例：")
    print(f"当前通信模式: {'STUDIO HTTP API' if USE_STUDIO else '标准IO'}")
    
    # 启动MCP服务器（STUDIO模式下不会启动本地进程）
    mcp_server = start_mcp_server()
    if not USE_STUDIO and not mcp_server:
        return
    
    try:
        # 示例1：用户说"帮我记录一笔35元的午餐费用"
        print("\n用户: 帮我记录一笔35元的午餐费用")
        parsed = parse_voice_command("帮我记录一笔35元的午餐费用")
        print(f"解析结果: {parsed}")  # 添加调试信息
        response = send_mcp_request(mcp_server, parsed["action"], parsed["params"])
        result = format_response(response, parsed["action"])
        print(f"小智: {result}")
        
        # 示例2：用户说"我的账户余额是多少？"
        print("\n用户: 我的账户余额是多少？")
        parsed = parse_voice_command("我的账户余额是多少？")
        print(f"解析结果: {parsed}")  # 添加调试信息
        response = send_mcp_request(mcp_server, parsed["action"], parsed["params"])
        result = format_response(response, parsed["action"])
        print(f"小智: {result}")
        
        # 示例3：用户说"我这个月花了多少钱？"
        print("\n用户: 我这个月花了多少钱？")
        parsed = parse_voice_command("我这个月花了多少钱？")
        print(f"解析结果: {parsed}")  # 添加调试信息
        response = send_mcp_request(mcp_server, parsed["action"], parsed["params"])
        result = format_response(response, parsed["action"])
        print(f"小智: {result}")
        
        # 示例4：用户说"最近7天的交易记录"
        print("\n用户: 最近7天的交易记录")
        parsed = parse_voice_command("最近7天的交易记录")
        print(f"解析结果: {parsed}")  # 添加调试信息
        response = send_mcp_request(mcp_server, parsed["action"], parsed["params"])
        result = format_response(response, parsed["action"])
        print(f"小智: {result}")
        
    finally:
        # 停止服务器（如果是标准模式）
        if not USE_STUDIO and mcp_server:
            mcp_server.terminate()
            mcp_server.wait(timeout=5)

def main():
    """主函数"""
    print("小智AI语音记账集成工具")
    print("=" * 50)
    
    print("\n正在运行小智AI服务器集成演示...")
    # 直接运行模拟演示模式，展示与小智AI服务器的集成效果
    simulate_xiaozhi_integration()
    
    print("\n程序已结束")

if __name__ == "__main__":
    main()