from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class KPICard(BaseModel):
    value: str
    percent: str
    trend: str
    subtext: str

class ChartData(BaseModel):
    name: str
    b2b: float
    b2c: float

class BestSeller(BaseModel):    
 # This was your primary crash point
    name: Optional[str] = "Unknown" 
    sales: Optional[int] = 0
    revenue: Optional[float] = 0.0

class DashboardOverviewResponse(BaseModel):
    revenue: KPICard
    orders: KPICard
    b2b_users: KPICard
    b2c_users: KPICard
    refunds: KPICard
    chart: List[ChartData]
    bestSellers: List[BestSeller]
    porter: List[Dict[str, Any]]

    class Config:
        from_attributes = True