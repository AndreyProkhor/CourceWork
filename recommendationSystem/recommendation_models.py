import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from main.models import ProductView
from .models import UserCluster, Product

#K-Means
def initialize_user_clusters():
    views = ProductView.objects.all().values('user', 'product', 'view_count')
    df = pd.DataFrame(views)
    pivot_table = df.pivot_table(index='user', columns='product', values='view_count', fill_value=0)
    num_users = pivot_table.shape[0]
    if num_users < 2:
        raise ValueError("Недостаточно юзеров для кластеризации.")
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(pivot_table)
    n_clusters = 2
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(scaled_data)
    for user, cluster in zip(pivot_table.index, clusters):
        UserCluster.objects.create(
            user_id=user,
            cluster=cluster,
            clustering_method='K-Means'
        )
    print("Юзеры успешно кластеризованы.")

def get_user_cluster(user_id):
    try:
        user_cluster = UserCluster.objects.get(user_id=user_id, clustering_method="K-Means")
        print(user_cluster.clustering_method)
        return user_cluster.cluster
    except UserCluster.DoesNotExist:
        print(f"Юзер с ID {user_id} не найден в кластерах. Начинаем кластеризацию.")
        UserCluster.objects.filter(clustering_method="K-Means").delete()
        initialize_user_clusters()
        try:
            user_cluster = UserCluster.objects.get(user_id=user_id, clustering_method="K-Means")
            return user_cluster.cluster
        except UserCluster.DoesNotExist:
            raise ValueError(f"Кластер для юзера с ID {user_id} не найден после кластеризации.")

#Cosine Similarity
def initialize_user_clusters_cosine_similarity():
    views = ProductView.objects.all().values('user', 'product', 'view_count')
    df = pd.DataFrame(views)
    pivot_table = df.pivot_table(index='user', columns='product', values='view_count', fill_value=0)
    similarity_matrix = cosine_similarity(pivot_table)
    n_clusters = 2
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(similarity_matrix)
    for user, cluster in zip(pivot_table.index, clusters):
        UserCluster.objects.create(
            user_id=user,
            cluster=cluster,
            clustering_method='Cosine Similarity'
        )
    print("Юзеры успешно кластеризованы.")

def get_user_cluster_cosine_similarity(user_id):
    try:
        user_cluster = UserCluster.objects.get(user_id=user_id, clustering_method="Cosine Similarity")
        print(user_cluster.clustering_method)
        return user_cluster.cluster
    except UserCluster.DoesNotExist:
        print(f"Юзер с ID {user_id} не найден в кластерах. Начинаем кластеризацию.")
        UserCluster.objects.filter(clustering_method="Cosine Similarity").delete()
        initialize_user_clusters_cosine_similarity()
        try:
            user_cluster = UserCluster.objects.get(user_id=user_id, clustering_method="Cosine Similarity")
            return user_cluster.cluster
        except UserCluster.DoesNotExist:
            raise ValueError(f"Кластер для юзера с ID {user_id} не найден после кластеризации.")
