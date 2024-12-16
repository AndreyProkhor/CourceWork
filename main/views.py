from django.shortcuts import render, get_object_or_404
from .models import Product, Category, ProductView
from django.core.paginator import Paginator
from cart.forms import CartAddProductForm
from django.db.models import Q 
from django.http import JsonResponse
from django.urls import reverse
import requests
from django.conf import settings
# Create your views here.


def popular_list(request):
    products = Product.objects.filter(available=True)[:3]
    return render(request,
                  'main/index/index.html',
                  {'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product,
                               slug=slug,
                               available=True)
    cart_product_form = CartAddProductForm
    if request.user.is_authenticated:
        product_view, created = ProductView.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'view_count': 1}
        )
        if not created: 
            product_view.view_count += 1
            product_view.save()
    return render(request,
                'main/product/detail.html',
                {'product': product,
                 'cart_product_form': cart_product_form})

def product_list(request, category_slug=None):
    page = request.GET.get('page', 1)
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    search_query = request.GET.get('search', '')
    recommended_products = []
    if request.user.is_authenticated:
        try:
            recommendation_model = request.user.recommendationModel
            url = reverse(settings.RECOMMENDATION_MODELS_URLS.get(recommendation_model, settings.RECOMMENDATION_MODELS_URLS_DEFAULT))
            full_url = request.build_absolute_uri(url)
            print(full_url)
            response = requests.get(f'{full_url}?user_id={request.user.id}')
            response.raise_for_status()
            data = response.json()
            recommended_products = data.get('recommended_products', [])
        except requests.RequestException as e:
            print(f"Ошибка при обращении к API рекомендаций: {e}")
    recommended_set = set(recommended_products)
    all_products = list(products)
    if search_query:
        all_products = [p for p in all_products if search_query.lower() in p.name.lower() or search_query.lower() in p.description.lower()]
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        all_products = [p for p in all_products if p.category == category]
    recommended_queryset = [p for p in all_products if p.name in recommended_set]
    other_queryset = [p for p in all_products if p.name not in recommended_set]
    sorted_products = recommended_queryset + other_queryset
    paginator = Paginator(sorted_products, 10)
    current_page = paginator.page(int(page))
    return render(request, 'main/product/list.html', {
        'category': category,
        'categories': categories,
        'products': current_page,
        'slug_url': category_slug,
    })

def search_products(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query), available=True)[:5]
    results = [{'id': product.id, 'name': product.name} for product in products]
    return JsonResponse(results, safe=False)