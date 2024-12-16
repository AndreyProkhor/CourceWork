from django.urls import path
from . import views 

app_name = 'forecasting'

urlpatterns = [
    path('forecast-orders/', views.forecast_orders, name='forecast_orders'),
]
