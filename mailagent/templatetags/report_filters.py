from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def filter_by_status(orders, status):
    return [order for order in orders if order.status == status]

@register.filter
def sum_total_cost(orders):
    return sum(order.get_total_cost() for order in orders)
