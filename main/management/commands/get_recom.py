from django.core.management.base import BaseCommand
from recommendationSystem.recommendation_models import initialize_user_clusters_cosine_similarity, get_user_cluster_cosine_similarity 
from main.models import Product, ProductView
from recommendationSystem.models import UserCluster
import pandas as pd

class Command(BaseCommand):
    help = 'Get product recommendations'

    def handle(self, *args, **kwargs):
        user_id = 3  
        print("\ntest_2\n")
        
        # Инициализация кластеров
        initialize_user_clusters_cosine_similarity()
        cluster = get_user_cluster_cosine_similarity(user_id)
        
        # Получение пользователей в том же кластере
        user_clusters = UserCluster.objects.filter(cluster=cluster).values_list('user', flat=True)
        
        # Получение всех просмотров продуктов
        views = ProductView.objects.all().values('user', 'product', 'view_count')
        df = pd.DataFrame(views)
        
        # Создание сводной таблицы
        pivot_table = df.pivot_table(index='user', columns='product', values='view_count', fill_value=0)
        recommended_products = pd.Series()
        
        # Получение просмотренных продуктов пользователями из того же кластера
        for similar_user in user_clusters:
            user_views = pivot_table.loc[similar_user]
            recommended_products = pd.concat([recommended_products, user_views[user_views > 0]])
        
        # Убираем дубликаты и сортируем
        recommended_products = recommended_products.groupby(recommended_products.index).sum().sort_values(ascending=False)
        
        # Получение идентификаторов продуктов
        product_ids = recommended_products.index.tolist()
        products = Product.objects.filter(id__in=product_ids)
        
        # Получение названий рекомендованных продуктов
        recommended_product_names = products.values_list('name', flat=True)
        
        # Вывод названий товаров
        print("Recommended Products:")
        for name in recommended_product_names:
            print(name)

        print("\ntest_2\n")