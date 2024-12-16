from django.db import models
from users.models import User
from main.models import Product

class UserCluster(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cluster = models.IntegerField()
    clustering_method = models.CharField(max_length=50, default="K-Means")

    def __str__(self):
        return f'User: {self.user.username}, Cluster: {self.cluster}, Method: {self.clustering_method}'