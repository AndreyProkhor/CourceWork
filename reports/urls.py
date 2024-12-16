from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('products/export/', views.export_products_excel, name='export_products_excel'),
    path('products/<int:id>/pdf/', views.generate_product_pdf, name='generate_product_pdf'),
    path('generate_pdf/<int:user_id>/', views.generate_pdf, name='generate_pdf'),
    path('generate_excel/<int:user_id>/', views.generate_excel, name='generate_excel'),
    path('category/<int:category_id>/products/export/', views.export_products_by_category, name='export_products_by_category'),
]