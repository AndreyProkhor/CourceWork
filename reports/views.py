import os
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from main.models import Product, Category
import xlsxwriter
from io import BytesIO
from django.contrib.auth.decorators import login_required
from PIL import Image
from django.conf import settings
from users.models import User
from orders.models import Order, OrderItem
import json
from datetime import datetime

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
    worksheet.set_column('A:A', 10) 
    worksheet.set_column('B:B', 30)  
    worksheet.set_column('C:C', 20) 
    worksheet.set_column('D:D', 15)  
    worksheet.set_column('E:E', 50)  
    worksheet.set_column('F:F', 40) 
    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'
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
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Price:</b> ${product.price}", normal_style))
    story.append(Spacer(1, 12))
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

def generate_excel(request, user_id):
    user = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=user)
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    headers = ['Order ID', 'Date', 'Status', 'Total Price', 'Items']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)
    for row, order in enumerate(orders, start=1):
        items_str = ", ".join([f"{item.product.name} (x{item.quantity})" for item in order.items.all()])
        worksheet.write(row, 0, order.id)
        worksheet.write(row, 1, order.created.strftime('%Y-%m-%d %H:%M:%S'))
        worksheet.write(row, 2, order.status)
        worksheet.write(row, 3, float(order.get_total_cost()))
        worksheet.write(row, 4, items_str)
    worksheet.set_column('A:A', 10) 
    worksheet.set_column('B:B', 20)  
    worksheet.set_column('C:C', 15)  
    worksheet.set_column('D:D', 15)  
    worksheet.set_column('E:E', 50)  
    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=orders_{user.username}.xlsx'
    return response

def generate_pdf(request, user_id):
    user = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=orders_{user.username}.pdf'
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph(f"Orders Report for {user.username}", title_style))
    story.append(Spacer(1, 12))
    for order in orders:
        story.append(Paragraph(f"Order #{order.id}", styles['Heading2']))
        story.append(Paragraph(f"Date: {order.created.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Status: {order.status}", styles['Normal']))
        story.append(Paragraph(f"Total Price: ${order.get_total_cost()}", styles['Normal']))
        story.append(Paragraph("Items:", styles['Heading4']))
        for item in order.items.all():
            story.append(Paragraph(
                f"• {item.product.name} - Quantity: {item.quantity}, Price: ${item.price}",
                styles['Normal']
            ))
        story.append(Spacer(1, 12))
    doc.build(story)
    return response

def export_products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'left',
        'valign': 'vcenter'
    })
    worksheet.write(0, 0, 'Category Details:', header_format)
    worksheet.write(1, 0, 'Name:', bold)
    worksheet.write(1, 1, category.name)
    worksheet.write(2, 0, 'Slug:', bold)
    worksheet.write(2, 1, category.slug)
    worksheet.write(3, 0, 'Total Products:', bold)
    worksheet.write(3, 1, products.count())
    current_row = 5
    headers = ['ID', 'Name', 'Price', 'Available', 'Description']
    for col, header in enumerate(headers):
        worksheet.write(current_row, col, header, bold)
    for row, product in enumerate(products, start=current_row + 1):
        worksheet.write(row, 0, product.id)
        worksheet.write(row, 1, product.name)
        worksheet.write(row, 2, float(product.price))
        worksheet.write(row, 3, 'Yes' if product.available else 'No')
        worksheet.write(row, 4, product.description)
    worksheet.set_column('A:A', 10)  
    worksheet.set_column('B:B', 30)  
    worksheet.set_column('C:C', 15) 
    worksheet.set_column('D:D', 15)  
    worksheet.set_column('E:E', 50)  
    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=products_in_{category.slug}.xlsx'
    return response