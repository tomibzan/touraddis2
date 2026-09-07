from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('dashboard/', views.inventory_dashboard, name='dashboard'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('low-stock-alerts/', views.low_stock_alerts, name='low_stock_alerts'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
]