"""数据模型定义"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """交易记录模型"""
    id: Optional[str] = None  # 交易ID，自动生成
    amount: float = Field(..., description="金额，正数为收入，负数为支出")
    category: str = Field(..., description="分类")
    description: Optional[str] = Field(None, description="描述")
    timestamp: datetime = Field(default_factory=datetime.now, description="交易时间")
    tags: List[str] = Field(default_factory=list, description="标签")


class Category(BaseModel):
    """分类模型"""
    name: str = Field(..., description="分类名称")
    type: str = Field(..., description="分类类型：income 或 expense")
    icon: Optional[str] = Field(None, description="分类图标")


class AccountSummary(BaseModel):
    """账户汇总信息"""
    total_balance: float = Field(..., description="总余额")
    total_income: float = Field(..., description="总收入")
    total_expense: float = Field(..., description="总支出")
    transaction_count: int = Field(..., description="交易笔数")


class MonthlySummary(BaseModel):
    """月度汇总信息"""
    month: str = Field(..., description="月份，格式：YYYY-MM")
    total_income: float = Field(..., description="月收入")
    total_expense: float = Field(..., description="月支出")
    balance_change: float = Field(..., description="余额变化")
    category_expenses: dict[str, float] = Field(..., description="各分类支出")