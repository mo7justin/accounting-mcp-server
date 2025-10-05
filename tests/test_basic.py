"""基本功能测试"""

import os
import sys
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from accounting_mcp.storage import StorageManager
from accounting_mcp.models import Transaction


def test_storage_basic():
    """测试存储的基本功能"""
    # 使用临时数据目录
    test_data_dir = "test_data"
    
    # 确保测试目录为空
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    
    # 创建存储管理器
    storage = StorageManager(test_data_dir)
    
    # 测试添加交易
    transaction = Transaction(
        amount=-35.5,
        category="food",
        description="午餐"
    )
    saved = storage.add_transaction(transaction)
    
    # 验证交易已保存
    assert saved.id is not None
    assert saved.amount == -35.5
    assert saved.category == "food"
    
    # 测试获取余额
    balance = storage.get_balance()
    assert balance == -35.5
    
    # 测试获取交易记录
    transactions = storage.get_transactions()
    assert len(transactions) == 1
    assert transactions[0].amount == -35.5
    
    # 清理测试数据
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    
    print("存储功能测试通过!")


if __name__ == "__main__":
    test_storage_basic()
    print("所有测试通过!")