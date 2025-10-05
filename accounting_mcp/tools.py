"""MCP工具实现"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict

from accounting_mcp.models import Transaction, MonthlySummary
from accounting_mcp.storage import StorageManager


class AccountingTools:
    """记账工具类，提供MCP接口"""
    
    def __init__(self):
        """初始化记账工具"""
        self.storage = StorageManager()
    
    def add_transaction(self, amount: float, category: str, 
                       description: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> Dict:
        """添加交易记录
        
        Args:
            amount: 金额，正数为收入，负数为支出
            category: 分类名称
            description: 交易描述
            tags: 标签列表
            
        Returns:
            包含交易信息和当前余额的字典
        """
        # 验证分类是否存在
        categories = [c.name for c in self.storage.get_categories()]
        if category not in categories:
            return {
                "success": False,
                "error": f"分类 '{category}' 不存在",
                "available_categories": categories
            }
        
        # 创建交易记录
        transaction = Transaction(
            amount=amount,
            category=category,
            description=description,
            tags=tags or []
        )
        
        # 保存交易
        saved_transaction = self.storage.add_transaction(transaction)
        current_balance = self.storage.get_balance()
        
        return {
            "success": True,
            "transaction": saved_transaction.model_dump(),
            "current_balance": current_balance,
            "message": f"已添加{'收入' if amount > 0 else '支出'}记录，当前余额: {current_balance:.2f}元"
        }
    
    def get_balance(self) -> Dict:
        """获取当前账户余额
        
        Returns:
            包含余额信息的字典
        """
        balance = self.storage.get_balance()
        return {
            "balance": balance,
            "message": f"当前账户余额为: {balance:.2f}元"
        }
    
    def list_transactions(self, category: Optional[str] = None,
                         days: Optional[int] = None) -> Dict:
        """查询交易记录
        
        Args:
            category: 按分类筛选
            days: 最近几天的交易
            
        Returns:
            包含交易列表的字典
        """
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)
        
        transactions = self.storage.get_transactions(
            category=category,
            start_date=start_date
        )
        
        return {
            "transactions": [t.model_dump() for t in transactions],
            "count": len(transactions),
            "message": f"共查询到{len(transactions)}条交易记录"
        }
    
    def get_monthly_summary(self, year: Optional[int] = None,
                          month: Optional[int] = None) -> Dict:
        """获取月度财务汇总
        
        Args:
            year: 年份，默认为当前年
            month: 月份，默认为当前月
            
        Returns:
            月度汇总信息
        """
        # 使用当前年月如果未指定
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        # 构建月份字符串
        month_str = f"{target_year:04d}-{target_month:02d}"
        
        # 计算月份的开始和结束时间
        start_date = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(target_year, target_month + 1, 1) - timedelta(seconds=1)
        
        # 获取该月的所有交易
        transactions = self.storage.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        # 计算收入和支出
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
        balance_change = total_income - total_expense
        
        # 按分类统计支出
        category_expenses: Dict[str, float] = {}
        for t in transactions:
            if t.amount < 0:  # 只统计支出
                if t.category not in category_expenses:
                    category_expenses[t.category] = 0
                category_expenses[t.category] += abs(t.amount)
        
        summary = MonthlySummary(
            month=month_str,
            total_income=total_income,
            total_expense=total_expense,
            balance_change=balance_change,
            category_expenses=category_expenses
        )
        
        return {
            "summary": summary.model_dump(),
            "message": f"{month_str}月度汇总: 收入{total_income:.2f}元，支出{total_expense:.2f}元，结余{balance_change:.2f}元"
        }


# 创建全局工具实例
accounting_tools = AccountingTools()

# 导出MCP工具函数
def add_transaction(**kwargs):
    return accounting_tools.add_transaction(**kwargs)

def get_balance(**kwargs):
    return accounting_tools.get_balance(**kwargs)

def list_transactions(**kwargs):
    return accounting_tools.list_transactions(**kwargs)

def get_monthly_summary(**kwargs):
    return accounting_tools.get_monthly_summary(**kwargs)