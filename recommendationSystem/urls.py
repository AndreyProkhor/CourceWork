from django.urls import path
from .views import recommend_products, recommend_product_cosine_similarity, \
    recommend_products_with_model

app_name = 'recommendationSystem'

urlpatterns = [
    path('recommend/', recommend_products, name='recommend_products'),
    path('recommend-cosine/', recommend_product_cosine_similarity, name='recommend_product_cosine_similarity'),
    path('social-recommend-model/', recommend_products_with_model, name='recommend_products_with_model'),
]