from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from .forms import UserLoginForm, UserRegistrationForm, \
    ProfileForm
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from orders.models import Order, OrderItem


def login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username,
                                     password=password)
            if user:
                auth.login(request, user)
                next_url = request.POST.get('next')
                print(next_url)
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect(reverse('main:product_list'))
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            messages.success(request, f'{user.username}, Successful Registration')
            return HttpResponseRedirect(reverse('user:login'))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/registration.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user,
                           files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile was changed')
            return HttpResponseRedirect(reverse('user:profile'))
    else:
        form = ProfileForm(instance=request.user)
    
    orders = Order.objects.filter(user=request.user).prefetch_related(
        Prefetch(
            'items',
            queryset=OrderItem.objects.select_related('product'),
        )
    ).order_by('-updated')
    return render(request, 'users/profile.html',
                  {'form': form,
                   'orders': orders})

@login_required
def get_expense_data(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).prefetch_related('items')
        data = []
        for order in orders:
            order_data = {
                'order_id': order.id,
                'created': order.created,
                'total_cost': order.get_total_cost(),
                'items': []
            }
            for item in order.items.all():
                item_data = {
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'cost': item.get_cost()
                }
                order_data['items'].append(item_data)
            data.append(order_data)
        return JsonResponse(data, safe=False)

def logout(request):
    auth.logout(request)
    return redirect(reverse('main:product_list'))
