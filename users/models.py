from django.db import models
from django.contrib.auth.models import  AbstractUser

class User(AbstractUser):
    image = models.ImageField(upload_to='users_image', blank=True,
                              null=True)
    recommendationModel = models.CharField(max_length=50, default='k-means') 

    

    class Meta:
        db_table = 'user'


    def __str__(self):
        return self.username

# Create your models here.
