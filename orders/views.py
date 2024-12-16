from django.shortcuts import render, redirect
from django.urls import reverse
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import weasyprint 

# Create your views here.
@login_required(login_url='user:login')
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, request=request)
        if form.is_valid():
            order = form.save()
            for item in cart:
                discounted_price = item['product'].sell_price()
                OrderItem.objects.create(order=order,
                                         product=item['product'],
                                         price = discounted_price,
                                         quantity=item['quantity'])
            cart.clear()
            request.session['order_id'] = order.id
            print(f'Order ID set in session: {order.id}')
            return redirect(reverse('payment:process'))
            # return render(request,
            #               'order/created.html',{
            #                   'order' : order,
            #                   'form': form
            #               })
    else:
        form = OrderCreateForm(request = request)
    return render(request,
                  'order/create.html',
                  {
                      'cart': cart,
                      'form': form
                  })


# @login_required(login_url='user:login')
# def order_pdf(request):
#     order_id = request.session.get('order_id')
#     order_items = OrderItem.objects.filter(order_id=order_id)
#     html = render_to_string('order/order_pdf.html', {'order_items': order_items})
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="order_{order_id}.pdf"'
#     pisa_status = pisa.CreatePDF(html, dest=response)
#     if pisa_status.err:
#         return HttpResponse('We had some errors <pre>' + html + '</pre>')
#     return response


@login_required(login_url='user:login')
def order_pdf(request):
    order_id = request.session.get('order_id')
    if not order_id:
        print(f'Order ID set in session: нету')
    
    order_items = OrderItem.objects.filter(order_id=order_id)
    html_string = render_to_string('order/order_pdf.html', {'order_items': order_items})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order_id}.pdf"'
    weasyprint.HTML(string=html_string).write_pdf(response,
                                                stylesheets=[weasyprint.CSS(
                                                    settings.STATIC_ROOT / 'css/base.css'
                                                )])
    return response