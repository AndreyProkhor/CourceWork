from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import io
from reportlab.lib.utils import ImageReader

from users.models import User
from main.models import Product, Category
from orders.models import Order, OrderItem
from recommendationSystem.models import UserCluster
from .forms import CategoryForm, ProductForm, UserForm, UserUpdateForm
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from django.conf import settings
import os
from PIL import Image
import io
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image as RLImage, Table, TableStyle
from io import BytesIO
from django.contrib import messages
import logging
from recommendationSystem.recommendation_models import initialize_user_clusters_cosine_similarity, initialize_user_clusters
from recommendationSystem.neural_recommendation_models import generate_recommendation_model
import plotly
import kaleido
import xlsxwriter
# Create your views here.


def user_list(request):
    search_query = request.GET.get('search', '')
    users = User.objects.all()
    if search_query:
        users = users.filter(username__icontains=search_query)
    return render(request, 'adminPanel/user_list.html', {'users': users})

def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:user_list')
    else:
        form = UserForm()
    return render(request, 'adminPanel/user_form.html', {'form': form})

def user_update(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'adminPanel/user_form.html', {'form': form})

def user_delete(request, id):
    user = get_object_or_404(User, id=id)
    
    if user.id == request.user.id:
        messages.error(request, "Вы не можете удалить свой аккаунт!")
        return redirect('adminPanel:user_list')
        
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Пользователь успешно удален.')
        return redirect('adminPanel:user_list')
    
    return render(request, 'adminPanel/user_confirm_delete.html', {'object': user})

def user_suggestions(request):
    search_query = request.GET.get('search', '')
    users = []
    if search_query:
        users = User.objects.filter(username__icontains=search_query).values('id', 'username')[:5]
    return JsonResponse(list(users), safe=False)

def generate_user_pdf(request, id):
    user = get_object_or_404(User, id=id)
    
    orders = Order.objects.filter(user=user).order_by('-created')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    
    elements.append(Paragraph(f'User Report: {user.username}', title_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph(f'Email: {user.email}', styles['Normal']))
    elements.append(Paragraph(f'Registration Date: {user.date_joined.strftime("%d.%m.%Y")}', styles['Normal']))
    elements.append(Spacer(1, 12))
    
    total_orders = orders.count()
    total_spent = sum(
        sum(item.price * item.quantity for item in order.items.all())
        for order in orders
    )
    
    elements.append(Paragraph(f'Total Orders: {total_orders}', styles['Normal']))
    elements.append(Paragraph(f'Total Spent: ${total_spent:.2f}', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    for order in orders:
        elements.append(Paragraph(f'Order #{order.id} from {order.created.strftime("%d.%m.%Y")}', styles['Heading2']))
        elements.append(Paragraph(f'Status: {order.status}', styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph('Products in order:', styles['Normal']))
        for item in order.items.all():
            elements.append(Paragraph(
                f'- {item.product.name}: {item.quantity} pcs x ${item.price:.2f} = ${(item.quantity * item.price):.2f}',
                styles['Normal']
            ))
        
        order_total = sum(item.quantity * item.price for item in order.items.all())
        elements.append(Paragraph(f'Order Total: ${order_total:.2f}', styles['Normal']))
        elements.append(Spacer(1, 20))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_report.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response

def export_users_excel(request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Date Joined', 'Recommendation Model']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    users = User.objects.all()

    for row, user in enumerate(users, start=1):
        worksheet.write(row, 0, user.id)
        worksheet.write(row, 1, user.username)
        worksheet.write(row, 2, user.email)
        worksheet.write(row, 3, user.first_name)
        worksheet.write(row, 4, user.last_name)
        worksheet.write(row, 5, user.date_joined.strftime("%d.%m.%Y"))
        worksheet.write(row, 6, user.recommendationModel)

    workbook.close()

    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=users.xlsx'
    return response


def product_list(request):
    search_query = request.GET.get('search', '')
    products = Product.objects.all()
    if search_query:
        products = products.filter(name__icontains=search_query)
    return render(request, 'adminPanel/product_list.html', {'products': products})

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:product_list')
    else:
        form = ProductForm()
    return render(request, 'adminPanel/product_form.html', {'form': form})

def product_update(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'adminPanel/product_form.html', {'form': form})

def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.delete()
        return redirect('adminPanel:product_list')
    return render(request, 'adminPanel/product_confirm_delete.html', {'product': product})

def product_suggestions(request):
    search_query = request.GET.get('search', '')
    products = Product.objects.filter(name__icontains=search_query)[:5]
    suggestions = [{'id': product.id, 'name': product.name} for product in products]
    return JsonResponse(suggestions, safe=False)


def category_list(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.all()
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    return render(request, 'adminPanel/category_list.html', {'categories': categories})

def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:category_list')
    else:
        form = CategoryForm()
    return render(request, 'adminPanel/category_form.html', {'form': form})

def category_update(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('adminPanel:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'adminPanel/category_form.html', {'form': form})

def category_delete(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.delete()
        return redirect('adminPanel:category_list')
    return render(request, 'adminPanel/category_confirm_delete.html', {'category': category})

def category_suggestions(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.filter(name__icontains=search_query)[:5]
    suggestions = [{'id': category.id, 'name': category.name} for category in categories]
    return JsonResponse(suggestions, safe=False)

def search_categories(request):
    term = request.GET.get('term', '')
    categories = Category.objects.filter(name__icontains=term)[:10]
    data = [{'id': category.id, 'name': category.name} for category in categories]
    return JsonResponse(data, safe=False)

def export_products_excel(request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})

    headers = ['ID', 'Name', 'Category', 'Price', 'Description', 'Image URL']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    products = Product.objects.all()
    for row, product in enumerate(products, start=1):
        worksheet.write(row, 0, product.id)
        worksheet.write(row, 1, product.name)
        worksheet.write(row, 2, product.category.name)
        worksheet.write(row, 3, float(product.price))
        worksheet.write(row, 4, product.description)
        worksheet.write(row, 5, product.image.url if product.image else '')

    worksheet.set_column('A:A', 10)  # ID
    worksheet.set_column('B:B', 30)  # Name
    worksheet.set_column('C:C', 20)  # Category
    worksheet.set_column('D:D', 15)  # Price
    worksheet.set_column('E:E', 50)  # Description
    worksheet.set_column('F:F', 40)  # Image URL

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'
    return response

def export_categories(request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})

    headers = ['ID', 'Name', 'Slug']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    categories = Category.objects.all()
    for row, category in enumerate(categories, start=1):
        worksheet.write(row, 0, category.id)
        worksheet.write(row, 1, category.name)
        worksheet.write(row, 2, category.slug)

    worksheet.set_column('A:A', 10)  # ID
    worksheet.set_column('B:B', 30)  # Name
    worksheet.set_column('C:C', 20)  # Slug

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=categories.xlsx'
    return response

def generate_product_pdf(request, id):
    product = get_object_or_404(Product, id=id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="product_{product.id}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    description_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        spaceBefore=12,
        spaceAfter=12,
        leading=16
    )
    
    story.append(Paragraph(f"Product Report: {product.name}", title_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"<b>Category:</b> {product.category.name}", normal_style))
    story.append(Paragraph(f"<b>Price:</b> ${product.price}", normal_style))
    story.append(Paragraph("<b>Description:</b>", normal_style))
    story.append(Paragraph(product.description, description_style))
    story.append(Spacer(1, 12))
    
    if product.image:
        img_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img = img.convert('RGB')
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            if img_width > 400:
                img_width = 400
                img_height = int(img_width * aspect)
            
            img_temp = BytesIO()
            img.save(img_temp, format='PNG')
            img_temp.seek(0)
            
            story.append(Paragraph("<b>Product Image:</b>", normal_style))
            story.append(Spacer(1, 12))
            story.append(RLImage(img_temp, width=img_width, height=img_height))
    
    doc.build(story)
    return response


def cluster_management(request):
    user_clusters = UserCluster.objects.select_related('user').all()
    cluster_numbers = range(2)  
    
    context = {
        'user_clusters': user_clusters,
        'cluster_numbers': cluster_numbers,
    }
    return render(request, 'adminPanel/cluster_management.html', context)

def update_user_cluster(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_cluster = data.get('cluster')
        method = update.get('method')
        try:
            cluster = UserCluster.objects.get(user_id=user_id, clustering_method=method)
            cluster.cluster = new_cluster
            cluster.save()
            return JsonResponse({'success': True})
        except UserCluster.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользовательский кластер не найден'})
    
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def update_user_clusters_batch(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            updates = data.get('updates', [])
            clusters_to_update = []
            for update in updates:
                user_id = update.get('user_id')
                new_cluster = update.get('cluster')
                method = update.get('method')
                try:
                    cluster = UserCluster.objects.get(user_id=user_id, clustering_method=method)
                    cluster.cluster = new_cluster
                    clusters_to_update.append(cluster)
                except UserCluster.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Юзерский кластер не найден для пользователя: {user_id} метод: {method}'
                    })
            if clusters_to_update:
                with transaction.atomic():
                    for cluster in clusters_to_update:
                        cluster.save()
                return JsonResponse({'success': True})
            return JsonResponse({
                'success': False,
                'error': 'Нет обновляемых кластеров'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON данных'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Неверный запрос'
    })

def run_kmeans_clustering(request):
    if request.method == 'POST':
        try:
            UserCluster.objects.filter(clustering_method='K-Means').delete()
            initialize_user_clusters()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def run_cosine_clustering(request):
    if request.method == 'POST':
        try:
            UserCluster.objects.filter(clustering_method='Cosine Similarity').delete()
            initialize_user_clusters_cosine_similarity()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def train_model(request):
    if request.method == 'POST':
        try:
            generate_recommendation_model()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def get_model_info(request):
    try:
        model_dir = os.path.join(settings.BASE_DIR, 'recommendationSystem', 'user_social_models')
        json_files = [f for f in os.listdir(model_dir) if f.endswith('.json')]
        
        if not json_files:
            return JsonResponse({
                'parameters': {
                    'error': 'Нет сохраненных моделей'
                },
                'performance': {
                    'timestamps': [],
                    'metrics': []
                }
            })
        
        latest_json = sorted(json_files)[-1]
        json_path = os.path.join(model_dir, latest_json)
        
        with open(json_path, 'r') as f:
            model_info = json.load(f)
        
        def format_timestamp(ts):
            if not ts:
                return ''
            ts = ts.split('_')
            if len(ts) != 2:
                return ts[0]
            date, time = ts
            return f"{date[6:8]}.{date[4:6]}.{date[2:4]} {time[:2]}:{time[2:4]}"

        readable_info = {
            'parameters': {
                'Model Type': 'Neural Network',
                'Test Loss': f"{model_info.get('test_loss', 0):.4f}",
                'Test Accuracy': f"{model_info.get('test_accuracy', 0):.4f}",
                'Last Update': format_timestamp(model_info.get('timestamp', ''))
            },
            'performance': {
                'timestamps': [format_timestamp(model_info.get('timestamp', ''))],
                'metrics': [model_info.get('test_accuracy', 0)]
            }
        }
        
        other_files = sorted([f for f in json_files if f != latest_json])
        for json_file in other_files[-4:]:
            file_path = os.path.join(model_dir, json_file)
            with open(file_path, 'r') as f:
                prev_info = json.load(f)
                readable_info['performance']['timestamps'].insert(0, format_timestamp(prev_info.get('timestamp', '')))
                readable_info['performance']['metrics'].insert(0, prev_info.get('test_accuracy', 0))
        
        return JsonResponse(readable_info)
    except Exception as e:
        return JsonResponse({
            'parameters': {
                'error': str(e)
            },
            'performance': {
                'timestamps': [],
                'metrics': []
            }
        })

def purchase_analysis(request):
    return render(request, 'adminPanel/purchase_analysis.html')

def get_user_purchases(request):
    login = request.GET.get('login')
    if not login:
        return JsonResponse({
            'success': False,
            'error': 'Необходимо указать логин пользователя'
        })

    try:
        user = User.objects.get(username=login)
        
        orders = Order.objects.filter(user=user)
        
        purchases = []
        for order in orders:
            for item in order.items.all():
                purchases.append({
                    'product_name': item.product.name,
                    'category_name': item.product.category.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'date': order.created.isoformat()
                })
        
        return JsonResponse({
            'success': True,
            'purchases': purchases
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Пользователь не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def generate_purchase_analysis_pdf(request):
    login = request.GET.get('login')
    if not login:
        return HttpResponse('Параметр "login" не указан', status=400)
    
    try:
        user = User.objects.get(username=login)
        orders = Order.objects.filter(user=user)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="purchase_analysis_{login}.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height-50, f"Purchase Analysis for {login}")
        
        y = height - 100
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Summary")
        
        total_spent = sum(sum(item.quantity * item.price for item in order.items.all()) for order in orders)
        total_orders = orders.count()
        total_items = sum(sum(item.quantity for item in order.items.all()) for order in orders)
        
        p.setFont("Helvetica", 12)
        y -= 30
        p.drawString(50, y, f"Total Orders: {total_orders}")
        y -= 20
        p.drawString(50, y, f"Total Items Purchased: {total_items}")
        y -= 20
        p.drawString(50, y, f"Total Amount Spent: ${total_spent:.2f}")

        y -= 40
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Spending by Category")

        category_spending = {}
        for order in orders:
            for item in order.items.all():
                category = item.product.category.name
                if category not in category_spending:
                    category_spending[category] = 0
                category_spending[category] += item.quantity * item.price

        if category_spending:
            plt.figure(figsize=(8, 4))
            plt.bar(category_spending.keys(), category_spending.values(), color='skyblue')
            plt.xticks(rotation=45, ha='right')
            plt.title('Spending by Category')
            plt.ylabel('Amount ($)')
            plt.tight_layout()

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            y -= 300 
            if y < 300:  
                p.showPage()
                y = height - 300
            p.drawImage(ImageReader(buffer), 50, y, width=500, height=250)
            y -= 30
        
        y -= 40
        if y < 100: 
            p.showPage()
            y = height - 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "Order Details")
        p.setFont("Helvetica", 12)
        
        for order in orders:
            if y < 100:  
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 12)
            
            y -= 30
            p.drawString(50, y, f"Order Date: {order.created.strftime('%d.%m.%Y')}")
            
            total_order_amount = 0
            for item in order.items.all():
                if y < 100:  
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)
                
                y -= 20
                amount = item.quantity * item.price
                total_order_amount += amount
                p.drawString(70, y, f"• {item.product.name} ({item.product.category.name})")
                y -= 20
                p.drawString(90, y, f"{item.quantity} x ${item.price:.2f} = ${amount:.2f}")
            
            y -= 25
            p.drawString(70, y, f"Total Order Amount: ${total_order_amount:.2f}")
            y -= 20
        
        p.showPage()
        p.save()
        return response
        
    except User.DoesNotExist:
        return HttpResponse('Пользователь не найден', status=404)
    except Exception as e:
        return HttpResponse(f'Ошибка при генерации PDF: {str(e)}', status=500)

def general_sales_analysis(request):
    return render(request, 'adminPanel/general_sales_analysis.html')

def profit_forecasting(request):
    categories = Category.objects.all()
    return render(request, 'adminPanel/profit_forecasting.html', {'categories': categories})

def order_management(request):
    if not request.user.is_authenticated:
        return redirect('main:index')
    if not request.user.is_staff:
        return redirect('main:index')
    return render(request, 'adminPanel/order_management.html')

def search_users(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Аутентификация необходима'}, status=401)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse([], safe=False)
        
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).values('id', 'username', 'email')[:10]
        
        return JsonResponse(list(users), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_user_orders(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Авторизация необходима'}, status=401)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
    try:
        orders = Order.objects.filter(user_id=user_id)
        return JsonResponse([{
            'id': order.id,
            'created': order.created,
            'total_cost': order.get_total_cost(),
            'status': order.status,
            'paid': order.paid
        } for order in orders], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_order_items(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Неавторизованный пользователь'}, status=403)
    
    try:
        order = Order.objects.get(id=order_id)
        items = []
        for item in order.items.all():
            items.append({
                'id': item.id,
                'product_name': item.product.name,
                'product_image': item.product.image.url if item.product.image else None,
                'quantity': item.quantity,
                'price': str(item.price),
                'total': str(item.get_cost())
            })
        return JsonResponse({'items': items})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Заказ не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def update_order_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Требуется аутентификация'}, status=401)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    
    try:
        data = json.loads(request.body)
        print('Полученные данные:', data)  
        
        updates = data.get('updates', [])
        if not updates:
            return JsonResponse({'error': 'Нет обновлений'}, status=400)
        
        print('Обработка обновлений:', updates)  
        success_updates = []
        
        with transaction.atomic():
            for update in updates:
                order_id = update.get('orderId')
                new_status = update.get('status')
                
                if not order_id or not new_status:
                    print(f'Неверные данные обновления: {update}')  
                    return JsonResponse({'error': f'Неверные данные обновления: {update}'}, status=400)
                
                if new_status not in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
                    print(f'Неверный статус: {new_status}') 
                    return JsonResponse({'error': f'Неверный статус: {new_status}'}, status=400)
                
                try:
                    order = Order.objects.get(id=order_id)
                    old_status = order.status
                    order.status = new_status
                    order.save()
                    success_updates.append({
                        'orderId': order_id,
                        'oldStatus': old_status,
                        'newStatus': new_status
                    })
                    print(f'Успешно обновлен заказ {order_id} старый статус: {old_status}. Новый статус {new_status}.')  # Отладочный вывод
                except Order.DoesNotExist:
                    print(f'Заказ {order_id} не найден')  
                    return JsonResponse({'error': f'Заказ {order_id} не найден'}, status=404)
        
        print(f'Все обновления выполнены: {success_updates}')  
        return JsonResponse({
            'success': True,
            'updates': success_updates
        })
    except json.JSONDecodeError as e:
        print(f'Неверный JSON: {str(e)}')  
        return JsonResponse({'error': 'Неверный JSON'}, status=400)
    except Exception as e:
        print(f'Неожиданная ошибка: {str(e)}')  
        return JsonResponse({'error': str(e)}, status=400)

def generate_order_reports(request):
    return render(request, 'adminPanel/generate_order_reports.html')

@login_required
def generate_orders_excel(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        orders = Order.objects.filter(status__in=['Pending', 'Processing']).order_by('created')
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Orders')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        alt_row_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#F2F2F2',
            'text_wrap': True
        })

        worksheet.set_column('A:A', 10)  # Order ID
        worksheet.set_column('B:B', 20)  # Customer
        worksheet.set_column('C:C', 40)  # Address
        worksheet.set_column('D:D', 50)  # Products
        worksheet.set_column('E:E', 15)  # Status

        headers = ['Order ID', 'Customer', 'Address', 'Products', 'Status']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        for row, order in enumerate(orders, start=1):
            products_list = [f"{item.product.name} (x{item.quantity})" for item in order.items.all()]
            
            row_format = cell_format if row % 2 == 0 else alt_row_format
            
            worksheet.write(row, 0, order.id, row_format)
            worksheet.write(row, 1, f"{order.first_name} {order.last_name}", row_format)
            worksheet.write(row, 2, f"{order.address}, {order.city}, {order.postal_code}", row_format)
            worksheet.write(row, 3, "\n".join(products_list), row_format)
            worksheet.write(row, 4, order.status, row_format)

        workbook.close()

        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=orders_collection_list.xlsx'
        output.close()

        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def order_report(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'adminPanel/order_report.html')
