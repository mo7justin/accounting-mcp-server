"""支持STUDIO通信的MCP服务器"""

import json
import os
import sys
import traceback
from datetime import datetime, date
from typing import Any, Dict
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# 添加当前目录到Python路径，以便能够导入accounting_mcp模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入MCP服务器核心功能
from accounting_mcp.server import MCPServer, DateTimeEncoder
from accounting_mcp.tools import accounting_tools

# 从配置文件加载环境变量
from dotenv import load_dotenv

# 加载配置文件
load_dotenv('config.env')

# 获取STUDIO配置 - 使用0.0.0.0作为默认主机以支持Docker容器网络
STUDIO_HOST = os.getenv('STUDIO_HOST', '0.0.0.0')
STUDIO_PORT = int(os.getenv('STUDIO_PORT', '8000'))
STUDIO_PROTOCOL = os.getenv('STUDIO_PROTOCOL', 'http')
ENABLE_STUDIO = os.getenv('ENABLE_STUDIO', 'true').lower() == 'true'
STUDIO_API_KEY = os.getenv('STUDIO_API_KEY', '')

# Docker环境下的日志配置
DOCKER_ENV = os.getenv('DOCKER_ENV', 'false').lower() == 'true'


class StudioRequestHandler(BaseHTTPRequestHandler):
    """处理STUDIO HTTP请求的处理器"""
    
    def __init__(self, *args, **kwargs):
        self.mcp_server = kwargs.pop('mcp_server')
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求，主要用于健康检查"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "accounting-mcp-server"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False, cls=DateTimeEncoder).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "error": "Not Found",
                "message": "请求的资源不存在"
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求，用于JSON-RPC通信"""
        # 验证API密钥（如果配置了）
        if STUDIO_API_KEY and self.headers.get('Authorization') != f'Bearer {STUDIO_API_KEY}':
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "error": "Unauthorized",
                "message": "无效的API密钥"
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            return
        
        # 读取请求体
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # 解析JSON请求
            request = json.loads(post_data.decode('utf-8'))
            
            # 使用MCP服务器处理请求
            if isinstance(request, list):
                # 批量请求
                responses = []
                for req in request:
                    response = self.mcp_server.handle_request(req)
                    if response and "id" in response:
                        responses.append(response)
                response_data = responses
            else:
                # 单个请求
                response_data = self.mcp_server.handle_request(request)
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, cls=DateTimeEncoder).encode('utf-8'))
            
        except json.JSONDecodeError as e:
            # 处理JSON解析错误
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"JSON解析错误: {str(e)}"},
                "id": None
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            # 处理其他错误
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}",
                    "data": traceback.format_exc()
                },
                "id": None
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法，输出到标准错误"""
        print(f"[{datetime.now().isoformat()}] {format % args}", file=sys.stderr)


def run_studio_server(mcp_server):
    """运行STUDIO HTTP服务器"""
    # 创建请求处理器工厂，传递MCP服务器实例
    handler_factory = lambda *args, **kwargs: StudioRequestHandler(*args, mcp_server=mcp_server, **kwargs)
    
    # 创建HTTP服务器
    server_address = (STUDIO_HOST, STUDIO_PORT)
    httpd = HTTPServer(server_address, handler_factory)
    
    print(f"STUDIO服务器已启动，监听地址: {STUDIO_PROTOCOL}://{STUDIO_HOST}:{STUDIO_PORT}", file=sys.stderr)
    print(f"健康检查地址: {STUDIO_PROTOCOL}://{STUDIO_HOST}:{STUDIO_PORT}/health", file=sys.stderr)
    print(f"API端点: {STUDIO_PROTOCOL}://{STUDIO_HOST}:{STUDIO_PORT}", file=sys.stderr)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSTUDIO服务器已停止", file=sys.stderr)
    except Exception as e:
        print(f"STUDIO服务器错误: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        httpd.server_close()


class StudioMCPRunner:
    """运行STUDIO和标准MCP服务器的主类"""
    
    def __init__(self):
        self.mcp_server = MCPServer()
        self.studio_thread = None
    
    def start_studio_server(self):
        """在后台线程启动STUDIO服务器"""
        if ENABLE_STUDIO:
            self.studio_thread = threading.Thread(target=run_studio_server, args=(self.mcp_server,), daemon=True)
            self.studio_thread.start()
            print("STUDIO通信已启用", file=sys.stderr)
        else:
            print("STUDIO通信未启用（通过配置禁用）", file=sys.stderr)
    
    def run_stdio_server(self):
        """运行标准输入输出MCP服务器"""
        self.mcp_server.run()
    
    def run(self):
        """运行主程序"""
        print("=== MCP记账服务器(支持STUDIO) ===", file=sys.stderr)
        print(f"STUDIO配置 - 主机: {STUDIO_HOST}, 端口: {STUDIO_PORT}, 协议: {STUDIO_PROTOCOL}", file=sys.stderr)
        
        # 启动STUDIO服务器
        self.start_studio_server()
        
        # 运行标准输入输出服务器
        self.run_stdio_server()


# 主程序入口
if __name__ == "__main__":
    runner = StudioMCPRunner()
    runner.run()