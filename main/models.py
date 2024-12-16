from django.db import models
from django.urls import reverse
from users.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=20,
                            unique=True)
    slug = models.SlugField(max_length=20,
                            unique=True)
    
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("main:product_list_by_category", 
                       args=[self.slug])
    
class Product(models.Model):
    category = models.ForeignKey(Category,
                                 related_name='products',
                                 on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    image = models.ImageField(upload_to='products/%Y/%m/%d',
                              blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
    available = models.BigIntegerField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    discount = models.DecimalField(default=0.00,
                                   max_digits=4,
                                   decimal_places=2)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created'])
        ]

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("main:product_detail", 
                       args=[self.slug])
    
    def sell_price(self):
        if self.discount:
            return round(self.price - self.price * self.discount / 100, 2)
        return self.price
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images',
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product/%Y/%m/%d', blank=True)


    def __str__(self):
        return f'{self.product.name} - {self.image.name}'
    

class ProductView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=0) 
    last_viewed = models.DateTimeField(auto_now=True) 

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} viewed {self.product.name} {self.view_count} times'