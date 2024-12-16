from django.urls import path
from . import views 

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('pdf/', views.order_pdf, name='order_pdf'),
]
