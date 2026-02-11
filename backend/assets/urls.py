from django.urls import path
from .views import MarketIndexView, StockSearchView

urlpatterns = [
    path("indices", MarketIndexView.as_view(), name="market-indices"),
    path("search",  StockSearchView.as_view(), name="stock-search"),
]
