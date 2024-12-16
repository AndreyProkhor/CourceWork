from django.http import JsonResponse
from django.shortcuts import render
from orders.models import Order
from main.models import Product, Category
from datetime import datetime, timedelta
from django.utils import timezone
from collections import defaultdict
from django.db.models import Sum, Count
from decimal import Decimal

def get_category_forecast(category_id):
    """
    Calculate forecast for a specific category based on order history
    """
    today = timezone.now()
    start_date = today - timedelta(days=30)  
    
    orders = Order.objects.filter(
        items__product__category_id=category_id,
        created__date__gte=start_date
    )
    
    daily_orders = orders.values('created__date').annotate(
        order_count=Count('id', distinct=True),
        total_amount=Sum('items__price')
    ).order_by('created__date')
    
    if not daily_orders:
        return {
            'average_orders': 0,
            'average_amount': 0,
            'trend': 'stable',
            'confidence': 0
        }
    
    total_days = (today - start_date).days
    total_orders = sum(day['order_count'] for day in daily_orders)
    total_amount = sum(day['total_amount'] or 0 for day in daily_orders)
    
    average_orders = total_orders / total_days if total_days > 0 else 0
    average_amount = float(total_amount) / total_days if total_days > 0 else 0
    
    if len(daily_orders) >= 2:
        recent_avg = sum(day['order_count'] for day in daily_orders[-7:]) / min(7, len(daily_orders))
        older_avg = sum(day['order_count'] for day in daily_orders[:-7]) / max(1, len(daily_orders)-7)
        
        if recent_avg > older_avg * 1.1:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
            
        confidence = min(abs(recent_avg - older_avg) / older_avg * 100, 100) if older_avg > 0 else 50
    else:
        trend = 'stable'
        confidence = 50
        
    return {
        'average_orders': average_orders,
        'average_amount': average_amount,
        'trend': trend,
        'confidence': confidence
    }

def forecast_orders(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        if not category_id:
            return JsonResponse({'success': False, 'error': 'Category ID is required'})
            
        try:
            category = Category.objects.get(id=category_id)
            forecast = get_category_forecast(category_id)
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            dates = []
            historical_revenue = []
            forecasted_revenue = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(date_str)
                
                daily_revenue = Order.objects.filter(
                    items__product__category=category,
                    created__date=current_date.date()
                ).aggregate(
                    total=Sum('items__price')
                )['total'] or 0
                
                historical_revenue.append(float(daily_revenue))
                
                if current_date > end_date - timedelta(days=7):
                    forecasted_revenue.append(float(forecast['average_amount']))
                else:
                    forecasted_revenue.append(None)
                
                current_date += timedelta(days=1)
            
            return JsonResponse({
                'success': True,
                'forecast': forecast,
                'dates': dates,
                'historical_revenue': historical_revenue,
                'forecasted_revenue': forecasted_revenue
            })
            
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
