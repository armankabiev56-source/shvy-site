from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Category, Application

def index(request):
    popular = Product.objects.all()[:8]
    return render(request, 'index.html', {'popular': popular})

def catalog(request):
    categories = Category.objects.all().order_by('order')
    return render(request, 'catalog.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'category_detail.html', {'category': category})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {
        'product': product,
        'popular': Product.objects.all()[:6]   # для модального окна
    })

def about(request):
    return render(request, 'about.html')

def contacts(request):
    return render(request, 'contacts.html')

def leave_application(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        product_id = request.POST.get('product')
        message = request.POST.get('message', '')

        product = None
        if product_id:
            product = Product.objects.filter(id=product_id).first()

        Application.objects.create(
            name=name,
            phone=phone,
            product=product,
            message=message
        )
        messages.success(request, '✅ Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.')
        return redirect('index')
    return redirect('index')