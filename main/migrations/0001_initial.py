# Generated by Django 4.2.16 on 2024-12-01 21:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('slug', models.SlugField(max_length=20, unique=True)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField()),
                ('image', models.ImageField(blank=True, upload_to='products/%Y/%m/%d')),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('available', models.BigIntegerField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=4)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='main.category')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['name'], name='main_catego_name_5111b9_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['id', 'slug'], name='main_produc_id_f4bffc_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='main_produc_name_168fc5_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['-created'], name='main_produc_created_4330ad_idx'),
        ),
    ]
