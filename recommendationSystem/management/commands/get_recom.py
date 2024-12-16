from django.core.management.base import BaseCommand
from recommendationSystem.recommendation_models import initialize_user_clusters_cosine_similarity, get_user_cluster_cosine_similarity 
from main.models import Product, ProductView

class Command(BaseCommand):
    help = 'Get product recommendations'

    def handle(self, *args, **kwargs):
        user_id = 3  
        print("\ntest_2\n")
        initialize_user_clusters_cosine_similarity()
        products = get_user_cluster_cosine_similarity(user_id)
        for product in products:
            self.stdout.write(product.name)
        print("\ntest_2\n")