"""MCP服务器主程序"""

import json
import sys
import traceback
from datetime import datetime, date
from typing import Any, Dict
import re
import os

from accounting_mcp.tools import accounting_tools
from accounting_mcp.storage import StorageManager
from dotenv import load_dotenv

# 加载配置文件
load_dotenv('config.env')


# 自定义JSON编码器，用于处理datetime对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class MCPServer:
    """MCP服务器实现JSON-RPC协议"""
    
    def __init__(self):
        """初始化MCP服务器"""
        # 加载配置
        self.storage_dir = os.getenv('DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        # 确保数据目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        self.tools = {
            "add_transaction": accounting_tools.add_transaction,
            "get_balance": accounting_tools.get_balance,
            "list_transactions": accounting_tools.list_transactions,
            "get_monthly_summary": accounting_tools.get_monthly_summary,
            "process_voice_command": self.process_voice_command  # 添加语音命令处理方法
        }
        
        # MCP资源定义
        self.resources = {
            "transactions://all": self._get_all_transactions,
            "categories://all": self._get_all_categories,
            "summary://current": self._get_current_summary
        }
        
        # 初始化存储管理器
        self.storage = StorageManager(self.storage_dir)
    
    def _get_all_transactions(self) -> Dict[str, Any]:
        """获取所有交易记录"""
        transactions = self.storage.get_transactions()
        return {
            "transactions": [t.model_dump() for t in transactions],
            "count": len(transactions)
        }
    
    def _get_all_categories(self) -> Dict[str, Any]:
        """获取所有分类"""
        categories = self.storage.get_categories()
        return {
            "categories": [c.model_dump() for c in categories],
            "count": len(categories)
        }
    
    def _get_current_summary(self) -> Dict[str, Any]:
        """获取当前汇总信息"""
        balance = self.storage.get_balance()
        monthly_summary = accounting_tools.get_monthly_summary()
        
        return {
            "balance": balance,
            "monthly_summary": monthly_summary["summary"]
        }
    
    def process_voice_command(self, command: str) -> Dict[str, Any]:
        """
        处理语音命令
        
        Args:
            command: 语音命令字符串
            
        Returns:
            命令处理结果
        """
        # 转换为小写，便于匹配
        command = command.lower()
        
        # 匹配余额查询
        if any(keyword in command for keyword in ["余额", "还有多少钱", "账户余额"]):
            result = accounting_tools.get_balance()
            return {
                "success": True,
                "response": result["message"],
                "data": result
            }
        
        # 匹配本月支出查询
        if any(keyword in command for keyword in ["本月花了", "本月支出", "这个月花了", "这个月支出"]):
            result = accounting_tools.get_monthly_summary()
            expense = result["summary"]["total_expense"]
            response = f"您这个月共支出{expense:.2f}元"
            return {
                "success": True,
                "response": response,
                "data": result
            }
        
        # 匹配最近交易查询
        match = re.search(r'最近(\d+)天的交易记录', command)
        if match:
            days = int(match.group(1))
            result = accounting_tools.list_transactions(days=days)
            
            # 构建响应消息
            if result["count"] == 0:
                response = f"最近{days}天没有交易记录"
            else:
                response = f"最近{days}天共有{result['count']}条交易记录"
                # 添加前3条交易详情
                for i, t in enumerate(result["transactions"][:3]):
                    desc = t.get("description", "未命名")
                    amount = t["amount"]
                    type_text = "收入" if amount > 0 else "支出"
                    response += f"\n{i+1}. {desc} - {type_text} {abs(amount):.2f}元"
                if result["count"] > 3:
                    response += f"\n... 等{result['count']-3}条更多记录"
            
            return {
                "success": True,
                "response": response,
                "data": result
            }
        
        # 匹配添加交易记录
        match = re.search(r'添加一?笔?交易[:：]?\s*(\w+)，?\s*(\d+(\.\d+)?)元', command)
        if match:
            description = match.group(1)
            amount = float(match.group(2))
            
            # 根据描述自动分类
            category = self._auto_classify(description)
            
            # 添加交易记录（默认作为支出，负数）
            result = accounting_tools.add_transaction(
                amount=-amount,  # 默认为支出
                category=category,
                description=description
            )
            
            return {
                "success": result["success"],
                "response": result.get("message", "添加交易记录失败"),
                "data": result
            }
        
        # 匹配显示所有类别
        if any(keyword in command for keyword in ["显示所有类别", "列出所有类别", "所有分类", "查看分类"]):
            categories = self.storage.get_categories()
            category_names = [c.name for c in categories]
            
            response = f"共有{len(category_names)}个分类：" + "、".join(category_names)
            
            return {
                "success": True,
                "response": response,
                "data": {
                    "categories": category_names,
                    "count": len(category_names)
                }
            }
        
        # 未能识别的命令
        return {
            "success": False,
            "response": "抱歉，我无法理解您的命令。请尝试其他方式表达，例如'我这个月花了多少钱'或'添加一笔交易：午餐，35元'",
            "error": "unrecognized_command"
        }
    
    def _auto_classify(self, description: str) -> str:
        """根据描述自动分类"""
        # 定义常用的描述到分类的映射
        category_map = {
            "午餐": "餐饮",
            "早餐": "餐饮",
            "晚餐": "餐饮",
            "饭": "餐饮",
            "吃": "餐饮",
            "外卖": "餐饮",
            "零食": "餐饮",
            "咖啡": "餐饮",
            "奶茶": "餐饮",
            "水果": "餐饮",
            "蔬菜": "餐饮",
            "超市": "日用",
            "购物": "购物",
            "衣服": "购物",
            "鞋": "购物",
            "交通": "交通",
            "打车": "交通",
            "公交": "交通",
            "地铁": "交通",
            "加油": "交通",
            "停车": "交通",
            "电影": "娱乐",
            "游戏": "娱乐",
            "旅游": "娱乐",
            "门票": "娱乐",
            "话费": "通讯",
            "手机": "通讯",
            "网费": "通讯",
            "电费": "水电",
            "水费": "水电",
            "燃气": "水电",
            "房租": "住房",
            "房贷": "住房",
            "工资": "收入",
            "奖金": "收入",
            "红包": "收入",
            "利息": "收入",
            "兼职": "收入",
            "医疗": "医疗",
            "药品": "医疗",
            "看病": "医疗",
            "挂号": "医疗",
            "学习": "教育",
            "培训": "教育",
            "书": "教育",
            "学费": "教育",
            "礼物": "人情",
            "红包": "人情",
            "请客": "人情"
        }
        
        # 尝试匹配分类
        for keyword, category in category_map.items():
            if keyword in description:
                # 确认分类是否存在
                categories = [c.name for c in self.storage.get_categories()]
                if category in categories:
                    return category
        
        # 默认分类为其他
        categories = [c.name for c in self.storage.get_categories()]
        return "其他" if "其他" in categories else categories[0] if categories else "未分类"
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理JSON-RPC请求
        
        Args:
            request: JSON-RPC请求对象
            
        Returns:
            JSON-RPC响应对象
        """
        try:
            # 验证请求格式
            if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "无效的JSON-RPC请求"},
                    "id": request.get("id")
                }
            
            # 获取请求ID
            request_id = request.get("id")
            
            # 处理工具调用
            if "method" in request:
                method = request["method"]
                params = request.get("params", {})
                
                # 检查方法是否存在
                if method not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"方法 '{method}' 不存在"},
                        "id": request_id
                    }
                
                # 调用工具方法
                try:
                    result = self.tools[method](**params)
                    return {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                except Exception as e:
                    # 处理方法执行错误
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32602,
                            "message": f"方法执行错误: {str(e)}",
                            "data": traceback.format_exc()
                        },
                        "id": request_id
                    }
            
            # 处理资源请求
            elif "resource" in request:
                resource = request["resource"]
                
                # 检查资源是否存在
                if resource not in self.resources:
                    return {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"资源 '{resource}' 不存在"},
                        "id": request_id
                    }
                
                # 获取资源
                try:
                    result = self.resources[resource]()
                    return {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32602,
                            "message": f"资源访问错误: {str(e)}"
                        },
                        "id": request_id
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "请求必须包含 method 或 resource 字段"},
                    "id": request_id
                }
        
        except Exception as e:
            # 处理系统错误
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}",
                    "data": traceback.format_exc()
                },
                "id": request.get("id")
            }
    
    def run(self):
        """运行服务器，从标准输入读取请求，输出响应"""
        print("MCP记账服务器已启动，等待请求...", file=sys.stderr)
        
        try:
            while True:
                # 读取输入
                line = sys.stdin.readline()
                if not line:
                    break
                
                # 去除行尾换行符
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # 解析JSON请求
                    request = json.loads(line)
                    
                    # 处理批量请求
                    if isinstance(request, list):
                        responses = []
                        for req in request:
                            response = self.handle_request(req)
                            if response and "id" in response:
                                responses.append(response)
                        if responses:
                            print(json.dumps(responses, ensure_ascii=False, cls=DateTimeEncoder))
                    else:
                        # 处理单个请求
                        response = self.handle_request(request)
                        if response:
                            print(json.dumps(response, ensure_ascii=False, cls=DateTimeEncoder))
                    
                    # 刷新输出
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    # 处理JSON解析错误
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"JSON解析错误: {str(e)}"},
                        "id": None
                    }
                    print(json.dumps(error_response, ensure_ascii=False, cls=DateTimeEncoder))
                    sys.stdout.flush()
                    
        except KeyboardInterrupt:
            print("\nMCP服务器已停止", file=sys.stderr)
        except Exception as e:
            print(f"服务器错误: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


# 主程序入口
if __name__ == "__main__":
    server = MCPServer()
    server.run()