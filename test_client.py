"""交互式测试客户端"""

import json
import subprocess
import sys
import time


class MCPTestClient:
    """MCP测试客户端"""
    
    def __init__(self):
        """初始化客户端"""
        self.server_process = None
    
    def start_server(self):
        """启动MCP服务器"""
        try:
            print("正在启动MCP服务器...")
            # 启动服务器进程
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "accounting_mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 等待服务器启动
            time.sleep(1)
            
            # 检查服务器是否正常启动
            if self.server_process.poll() is not None:
                print("服务器启动失败!")
                error = self.server_process.stderr.read()
                print(f"错误信息: {error}")
                return False
            
            print("MCP服务器启动成功!")
            return True
            
        except Exception as e:
            print(f"启动服务器时发生错误: {e}")
            return False
    
    def stop_server(self):
        """停止MCP服务器"""
        if self.server_process:
            print("正在停止MCP服务器...")
            try:
                self.server_process.stdin.close()
                self.server_process.stdout.close()
                self.server_process.stderr.close()
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception as e:
                print(f"停止服务器时发生错误: {e}")
            finally:
                self.server_process = None
    
    def send_request(self, method, params=None, request_id=1):
        """发送JSON-RPC请求到服务器"""
        if not self.server_process:
            print("服务器未启动!")
            return None
        
        # 构建请求
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        
        if params:
            request["params"] = params
        
        # 发送请求
        request_str = json.dumps(request, ensure_ascii=False) + '\n'
        
        try:
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # 读取响应
            response_str = self.server_process.stdout.readline()
            if response_str:
                return json.loads(response_str)
            else:
                return None
                
        except Exception as e:
            print(f"发送请求时发生错误: {e}")
            return None
    
    def interactive_mode(self):
        """交互式测试模式"""
        print("\n=== MCP记账工具测试客户端 ===")
        print("输入 'help' 查看可用命令，输入 'exit' 退出")
        
        while True:
            command = input("\n> ").strip().lower()
            
            if command == 'exit':
                break
            elif command == 'help':
                self.show_help()
            elif command == 'balance':
                # 查询余额
                response = self.send_request("get_balance")
                self.print_response(response)
            elif command == 'list':
                # 列出交易记录
                days = input("查看最近几天的记录? (默认为30天): ").strip()
                days = int(days) if days else 30
                response = self.send_request("list_transactions", {"days": days})
                self.print_response(response)
            elif command.startswith('add'):
                # 添加交易记录
                self.add_transaction_interactive()
            elif command.startswith('month'):
                # 查看月度汇总
                self.show_monthly_summary_interactive()
            else:
                print(f"未知命令: {command}")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n可用命令:")
        print("  balance     - 查询当前余额")
        print("  list        - 列出交易记录")
        print("  add         - 添加交易记录")
        print("  month       - 查看月度财务汇总")
        print("  help        - 显示帮助信息")
        print("  exit        - 退出程序")
    
    def add_transaction_interactive(self):
        """交互式添加交易记录"""
        try:
            amount_str = input("金额 (正数为收入，负数为支出): ")
            amount = float(amount_str)
            
            category = input("分类 (food/transport/shopping/entertainment/salary/bonus/investment): ")
            description = input("描述 (可选): ")
            
            params = {
                "amount": amount,
                "category": category,
            }
            
            if description:
                params["description"] = description
            
            response = self.send_request("add_transaction", params)
            self.print_response(response)
            
        except ValueError:
            print("请输入有效的数字金额!")
    
    def show_monthly_summary_interactive(self):
        """交互式查看月度汇总"""
        year_str = input("年份 (留空表示当前年): ").strip()
        month_str = input("月份 (留空表示当前月): ").strip()
        
        params = {}
        if year_str:
            params["year"] = int(year_str)
        if month_str:
            params["month"] = int(month_str)
        
        response = self.send_request("get_monthly_summary", params)
        self.print_response(response)
    
    def print_response(self, response):
        """打印响应结果"""
        if not response:
            print("无响应")
            return
        
        if "error" in response:
            print(f"错误: {response['error']['message']}")
        else:
            result = response.get("result", {})
            # 打印消息
            if "message" in result:
                print(f"消息: {result['message']}")
            # 打印交易列表
            if "transactions" in result:
                print("\n交易记录:")
                for t in result["transactions"]:
                    print(f"  [{t['timestamp']}] {t['category']}: {t['amount']:.2f}元 - {t.get('description', '')}")
            # 打印汇总信息
            if "summary" in result:
                summary = result["summary"]
                print(f"\n月度汇总 ({summary['month']}):")
                print(f"  收入: {summary['total_income']:.2f}元")
                print(f"  支出: {summary['total_expense']:.2f}元")
                print(f"  结余: {summary['balance_change']:.2f}元")
                if summary['category_expenses']:
                    print("  分类支出:")
                    for cat, amount in summary['category_expenses'].items():
                        print(f"    {cat}: {amount:.2f}元")


def main():
    """主函数"""
    client = MCPTestClient()
    
    try:
        # 启动服务器
        if not client.start_server():
            return
        
        # 运行交互式模式
        client.interactive_mode()
        
    finally:
        # 确保服务器被停止
        client.stop_server()


if __name__ == "__main__":
    main()