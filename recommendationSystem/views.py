from django.shortcuts import render
from django.http import JsonResponse
from .models import UserCluster
from main.models import ProductView, Product
from .recommendation_models import get_user_cluster, get_user_cluster_cosine_similarity
from .neural_recommendation_models import load_latest_model_and_recommend
import pandas as pd

#K-Means
def recommend_products(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)
    try:
        cluster = get_user_cluster(user_id)
        user_clusters = UserCluster.objects.filter(cluster=cluster).values_list('user', flat=True)
        recommended_product_views = ProductView.objects.filter(user__in=user_clusters)
        recommended_products = recommended_product_views.values_list('product__name', flat=True).distinct()
        return JsonResponse({'recommended_products': list(recommended_products)})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)

#Cosine similarity
def recommend_product_cosine_similarity(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)
    try:
        cluster = get_user_cluster_cosine_similarity(user_id)
        user_clusters = UserCluster.objects.filter(cluster=cluster).values_list('user', flat=True)
        views = ProductView.objects.all().values('user', 'product', 'view_count')
        df = pd.DataFrame(views)
        pivot_table = df.pivot_table(index='user', columns='product', values='view_count', fill_value=0)
        recommended_products = pd.Series(dtype=int)
        for similar_user in user_clusters:
            user_views = pivot_table.loc[similar_user]
            user_views = user_views[user_views > 0]
            if not user_views.empty:
                recommended_products = pd.concat([recommended_products, user_views])
        recommended_products = recommended_products.groupby(recommended_products.index).sum().sort_values(ascending=False)
        product_ids = recommended_products.index.tolist()
        products = Product.objects.filter(id__in=product_ids)
        recommended_product_names = products.values_list('name', flat=True)
        return JsonResponse({'recommended_products': list(recommended_product_names)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)
    
#neural_model
def recommend_products_with_model(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)
    try:
        recommendations = load_latest_model_and_recommend(user_id)
        return JsonResponse({'recommended_products': recommendations})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)