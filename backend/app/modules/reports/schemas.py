from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Dict, Any, Optional

class SalesChartData(BaseModel):
    name: str
    sales: float
    orders: int

class SalesStats(BaseModel):
    total_sales: float
    total_orders: int
    avg_order_value: float

class SalesReportResponse(BaseModel):
    stats: SalesStats
    chart: List[SalesChartData]
    top_products: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)

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
# Optional[str] allows the name to be None without crashing
    name: Optional[str] = "Unknown" 
    
    # Setting defaults to 0 ensures that if the DB returns NULL, 
    # your API still sends a valid number to the frontend.
    sales: Optional[int] = 0
    revenue: Optional[float] = 0.0

class DashboardOverviewResponse(BaseModel):
    revenue: KPICard
    orders: KPICard
    users: KPICard
    refunds: KPICard
    chart: List[ChartData]
    bestSellers: List[BestSeller]
    porter: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)