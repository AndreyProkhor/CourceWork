# Generated by Django 4.2.16 on 2024-12-03 22:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created']},
        ),
    ]
