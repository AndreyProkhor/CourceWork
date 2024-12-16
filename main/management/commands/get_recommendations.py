from django.core.management.base import BaseCommand
from main.recomend_delete_after_test   import get_recommendations, get_recommendations_kmean 
from main.models import Product, ProductView

class Command(BaseCommand):
    help = 'Get product recommendations'

    def handle(self, *args, **kwargs):
        user_id = 3  
        admin_views = ProductView.objects.filter(user_id=user_id)
        print(admin_views.count())
        products = get_recommendations(user_id)
        for product in products:
            self.stdout.write(product.name)
        print("\ntest_2\n")
        products = get_recommendations_kmean(user_id)
        for product in products:
            self.stdout.write(product.name)