from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.reports_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('products/', views.product_performance, name='product_performance'),
    path('bookings/', views.booking_report, name='booking_report'),
    path('export/sales/', views.export_sales_csv, name='export_sales_csv'),
]