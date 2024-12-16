from django.core.management.base import BaseCommand
from recommendationSystem.recommendation_models import initialize_user_clusters_cosine_similarity, get_user_cluster_cosine_similarity 
from main.models import Product, ProductView
from recommendationSystem.models import UserCluster
import pandas as pd
import json
import pandas as pd
import numpy as np
import tensorflow as tf
import os
from sklearn.model_selection import train_test_split
from main.models import ProductView, Product
from datetime import datetime 
from django.conf import settings
from tqdm import tqdm

model_dir = os.path.join(settings.BASE_DIR, 'recommendationSystem', 'user_social_models')


class Command(BaseCommand):
    help = 'Get product recommendations'

    def handle(self, *args, **kwargs):
        # views = ProductView.objects.all().values('user', 'product', 'view_count')
        # df = pd.DataFrame(views)
        # if df.empty:
        #     raise ValueError("No data available for training the model.")
        # user_product_matrix = df.pivot(index='user', columns='product', values='view_count').fillna(0)
        # X = user_product_matrix.values
        # y = np.where(X > 0, 1, 0)
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        # model = tf.keras.Sequential([
        #     tf.keras.layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
        #     tf.keras.layers.Dense(64, activation='relu'),
        #     tf.keras.layers.Dense(y_train.shape[1], activation='sigmoid')
        # ])
        # model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        # model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.1)
        # test_loss, test_accuracy = model.evaluate(X_test, y_test)
        # print(f"Test loss: {test_loss:.4f}, Test accuracy: {test_accuracy:.4f}")
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # model_filename = f'{model_dir}/recommendation_model_{timestamp}.keras'
        # model.save(model_filename)
        # model_info = {
        #     'timestamp': timestamp,
        #     'test_loss': float(test_loss),
        #     'test_accuracy': float(test_accuracy)
        # }
        # with open(f'{model_dir}/model_info_{timestamp}.json', 'w') as json_file:
        #     json.dump(model_info, json_file, indent=4)
        # print(f"Recommendation model successfully generated and saved as {model_filename}.")
        model_files = [f for f in os.listdir(model_dir) if f.endswith('.keras')]
        if not model_files:
            print("No models found. Generating a new model.")
            return
            #generate_recommendation_model()
            #model_files = [f for f in os.listdir(model_dir) if f.endswith('.keras')]
        model_files.sort(key=lambda x: os.path.getmtime(os.path.join(model_dir, x)))
        latest_model_file = os.path.join(model_dir, model_files[-1])
        model = tf.keras.models.load_model(latest_model_file)
        views = ProductView.objects.all().values('user', 'product', 'view_count')
        df = pd.DataFrame(views)
        user_id = 3
        user_product_matrix = df.pivot(index='user', columns='product', values='view_count').fillna(0)
        if user_id not in user_product_matrix.index:
            print(f"User ID {user_id} not found in the user-product matrix. Generating a new model.")
            #generate_recommendation_model()
            #model_files = [f for f in os.listdir(model_dir) if f.endswith('.keras')]
            #model_files.sort(key=lambda x: os.path.getmtime(os.path.join(model_dir, x)))
            #latest_model_file = os.path.join(model_dir, model_files[-1])
            #model = tf.keras.models.load_model(latest_model_file)
            return
        user_vector = user_product_matrix.loc[user_id].values.reshape(1, -1)
        predictions = model.predict(user_vector).flatten()
        product_ids = user_product_matrix.columns
        top_n = 5
        recommended_indices = np.argsort(predictions)[20][::-1]
        recommended_product_ids = product_ids[recommended_indices]
        recommended_products = Product.objects.filter(id__in=recommended_product_ids)
        for x in recommended_products:
            print(f"\n{x.name}")