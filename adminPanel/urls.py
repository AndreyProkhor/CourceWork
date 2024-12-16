from django.urls import path
from . import views 

app_name = 'adminPanel'

urlpatterns = [
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/update/<int:id>/', views.category_update, name='category_update'),
    path('categories/delete/<int:id>/', views.category_delete, name='category_delete'),
    path('categories/suggestions/', views.category_suggestions, name='category_suggestions'),
    path('categories/export/', views.export_categories, name='export_categories'),
    path('api/categories/search/', views.search_categories, name='search_categories'),
    
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/update/<int:id>/', views.product_update, name='product_update'),
    path('products/delete/<int:id>/', views.product_delete, name='product_delete'),
    path('products/suggestions/', views.product_suggestions, name='product_suggestions'),
    path('products/<int:id>/pdf/', views.generate_product_pdf, name='generate_product_pdf'),
    path('products/export/', views.export_products_excel, name='export_products_excel'),
    
    # User URLs
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:id>/update/', views.user_update, name='user_update'),
    path('users/<int:id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:id>/pdf/', views.generate_user_pdf, name='generate_user_pdf'),
    path('users/suggestions/', views.user_suggestions, name='user_suggestions'),
    path('users/export/excel/', views.export_users_excel, name='export_users_excel'),
    path('api/users/search/', views.search_users, name='search_users'),
    
    # Cluster URLs
    path('clusters/', views.cluster_management, name='cluster_management'),
    path('clusters/update/', views.update_user_cluster, name='update_user_cluster'),
    path('clusters/update-batch/', views.update_user_clusters_batch, name='update_user_clusters_batch'),
    path('clusters/kmeans/', views.run_kmeans_clustering, name='run_kmeans_clustering'),
    path('clusters/cosine/', views.run_cosine_clustering, name='run_cosine_clustering'),
    
    # Model URLs
    path('model/train/', views.train_model, name='train_model'),
    path('model/info/', views.get_model_info, name='get_model_info'),
    
    # Purchase Analysis URLs
    path('purchase-analysis/', views.purchase_analysis, name='purchase_analysis'),
    path('purchase-analysis/user/', views.get_user_purchases, name='get_user_purchases'),
    path('purchase-analysis/pdf/', views.generate_purchase_analysis_pdf, name='generate_purchase_analysis_pdf'),
    
    # Sales Analysis URLs
    path('sales-analysis/', views.general_sales_analysis, name='general_sales_analysis'),
    
    # Profit Forecast URLs
    path('profit-forecast/', views.profit_forecasting, name='profit_forecasting'),
    
    # Order URLs
    path('orders/', views.order_management, name='order_management'),
    path('order-report/', views.order_report, name='order_report'),
    path('order-reports/', views.generate_order_reports, name='generate_order_reports'),
    path('api/orders/user/<int:user_id>/', views.get_user_orders, name='get_user_orders'),
    path('api/orders/update-status/', views.update_order_status, name='update_order_status'),
    path('api/orders/<int:order_id>/items/', views.get_order_items, name='get_order_items'),
    # path('api/orders/generate-pdf/', views.generate_orders_pdf, name='generate_orders_pdf'),
    path('api/orders/generate-excel/', views.generate_orders_excel, name='generate_orders_excel'),
]
