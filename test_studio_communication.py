#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
STUDIO通信模式测试脚本

此脚本用于测试STUDIO通信模式是否正常工作，包括健康检查和API调用。
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 加载配置
load_dotenv('config.env')

# 获取STUDIO配置
STUDIO_HOST = os.getenv('STUDIO_HOST', 'localhost')
STUDIO_PORT = os.getenv('STUDIO_PORT', '8000')
STUDIO_PROTOCOL = os.getenv('STUDIO_PROTOCOL', 'http')
STUDIO_API_KEY = os.getenv('STUDIO_API_KEY', '')
STUDIO_URL = f"{STUDIO_PROTOCOL}://{STUDIO_HOST}:{STUDIO_PORT}"


def test_health_check():
    """
    测试健康检查端点
    """
    print("\n=== 测试健康检查 ===")
    health_url = f"{STUDIO_URL}/health"
    
    try:
        # 设置请求头
        headers = {}
        if STUDIO_API_KEY:
            headers['Authorization'] = f'Bearer {STUDIO_API_KEY}'
        
        # 发送请求
        print(f"发送健康检查请求到: {health_url}")
        response = requests.get(health_url, headers=headers, timeout=5)
        
        # 显示结果
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("健康检查成功！")
            return True
        else:
            print("健康检查失败！")
            return False
    except Exception as e:
        print(f"健康检查出错: {str(e)}")
        return False


def test_mcp_api():
    """
    测试MCP API
    """
    print("\n=== 测试MCP API ===")
    api_url = STUDIO_URL
    
    # 测试命令列表
    test_commands = [
        "我这个月花了多少钱？",
        "显示所有类别"
    ]
    
    success_count = 0
    
    for command in test_commands:
        print(f"\n测试命令: {command}")
        
        # 构建请求
        request = {
            "jsonrpc": "2.0",
            "method": "process_voice_command",
            "params": {"command": command},
            "id": 1
        }
        
        try:
            # 设置请求头
            headers = {
                'Content-Type': 'application/json'
            }
            if STUDIO_API_KEY:
                headers['Authorization'] = f'Bearer {STUDIO_API_KEY}'
            
            # 发送请求
            print(f"发送请求到: {api_url}")
            response = requests.post(
                api_url,
                json=request,
                headers=headers,
                timeout=10
            )
            
            # 显示结果
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            
            if response.status_code == 200:
                success_count += 1
                print("命令执行成功！")
            else:
                print("命令执行失败！")
        except Exception as e:
            print(f"API调用出错: {str(e)}")
    
    # 总结
    print(f"\n测试总结: {success_count}/{len(test_commands)} 命令执行成功")
    return success_count == len(test_commands)


def main():
    """
    主函数
    """
    print("=== STUDIO通信模式测试工具 ===")
    print(f"当前STUDIO配置:")
    print(f"  服务器URL: {STUDIO_URL}")
    print(f"  API密钥: {'已设置' if STUDIO_API_KEY else '未设置'}")
    
    # 首先进行健康检查
    health_ok = test_health_check()
    
    # 如果健康检查成功，测试API
    if health_ok:
        api_ok = test_mcp_api()
        
        # 最终结果
        if api_ok:
            print("\n🎉 STUDIO通信测试全部通过！")
            return 0
        else:
            print("\n❌ STUDIO API测试部分失败。")
            return 1
    else:
        print("\n❌ STUDIO服务器连接失败，无法进行API测试。")
        print("请确保:")
        print("  1. STUDIO服务器已启动")
        print("  2. 配置的主机和端口正确")
        print("  3. 防火墙未阻止连接")
        return 1


if __name__ == "__main__":
    sys.exit(main())