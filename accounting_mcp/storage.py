"""数据存储管理"""

import json
import os
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from accounting_mcp.models import Transaction, Category, AccountSummary


class StorageManager:
    """存储管理器，负责数据的存取操作"""
    
    def __init__(self, data_dir: str = "data"):
        """初始化存储管理器"""
        self.data_dir = data_dir
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        self.categories_file = os.path.join(data_dir, "categories.json")
        self.account_file = os.path.join(data_dir, "account.json")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        # 初始化默认分类
        if not os.path.exists(self.categories_file):
            default_categories = [
                {"name": "food", "type": "expense", "icon": "🍔"},
                {"name": "transport", "type": "expense", "icon": "🚗"},
                {"name": "shopping", "type": "expense", "icon": "🛍️"},
                {"name": "entertainment", "type": "expense", "icon": "🎬"},
                {"name": "salary", "type": "income", "icon": "💼"},
                {"name": "bonus", "type": "income", "icon": "🎁"},
                {"name": "investment", "type": "income", "icon": "📈"},
            ]
            self._save_json(self.categories_file, default_categories)
        
        # 初始化账户信息
        if not os.path.exists(self.account_file):
            default_account = {"total_balance": 0.0}
            self._save_json(self.account_file, default_account)
        
        # 初始化交易记录文件
        if not os.path.exists(self.transactions_file):
            self._save_json(self.transactions_file, [])
    
    def _save_json(self, file_path: str, data: any):
        """保存数据到JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
    
    def _load_json(self, file_path: str, default: any = None):
        """从JSON文件加载数据"""
        try:
            if not os.path.exists(file_path):
                return default or []
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return default or []
    
    def add_transaction(self, transaction: Transaction) -> Transaction:
        """添加交易记录"""
        # 生成唯一ID
        if not transaction.id:
            transaction.id = str(uuid4())
        
        # 加载现有交易记录
        transactions = self._load_json(self.transactions_file)
        
        # 添加新交易
        transactions.append(transaction.model_dump())
        
        # 保存更新后的交易记录
        self._save_json(self.transactions_file, transactions)
        
        # 更新账户余额
        account_data = self._load_json(self.account_file, {"total_balance": 0.0})
        account_data["total_balance"] += transaction.amount
        self._save_json(self.account_file, account_data)
        
        return transaction
    
    def get_transactions(self, category: Optional[str] = None, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Transaction]:
        """获取交易记录，支持筛选"""
        transactions = self._load_json(self.transactions_file)
        result = []
        
        for t in transactions:
            # 转换时间字符串为datetime对象
            t_datetime = datetime.fromisoformat(t["timestamp"])
            
            # 应用筛选条件
            if category and t["category"] != category:
                continue
            if start_date and t_datetime < start_date:
                continue
            if end_date and t_datetime > end_date:
                continue
            
            result.append(Transaction(**t))
        
        # 按时间倒序排序
        result.sort(key=lambda x: x.timestamp, reverse=True)
        return result
    
    def get_categories(self) -> List[Category]:
        """获取所有分类"""
        categories_data = self._load_json(self.categories_file)
        return [Category(**c) for c in categories_data]
    
    def get_balance(self) -> float:
        """获取当前余额"""
        account_data = self._load_json(self.account_file, {"total_balance": 0.0})
        return account_data.get("total_balance", 0.0)
    
    def get_summary(self) -> AccountSummary:
        """获取账户汇总信息"""
        transactions = self.get_transactions()
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
        total_balance = self.get_balance()
        
        return AccountSummary(
            total_balance=total_balance,
            total_income=total_income,
            total_expense=total_expense,
            transaction_count=len(transactions)
        )