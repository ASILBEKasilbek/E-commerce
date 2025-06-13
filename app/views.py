from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Wishlist, Review, Order, OrderItem, Coupon
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal  # Decimal uchun import qo'shildi

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ro'yxatdan o'tdingiz! Endi tizimga kiring.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})

def product_list(request, slug=None):
    query = request.GET.get('q', '')
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)

    if slug:
        category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=category)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': category,
        'query': query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(slug=slug)[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} savatga qo'shildi!")
    return redirect('product_list')

@login_required
def remove_from_cart(request, pk):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product__pk=pk)
    cart_item.delete()
    messages.success(request, "Mahsulot savatdan o'chirildi!")
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'shop/cart.html', {'cart': cart})

@login_required
def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"{product.name} sevimlilarga qo'shildi!")
    else:
        messages.info(request, f"{product.name} allaqachon sevimlilarda!")
    return redirect('product_detail', slug=product.slug)

@login_required
def remove_from_wishlist(request, pk):
    wishlist = get_object_or_404(Wishlist, user=request.user, product__pk=pk)
    wishlist.delete()
    messages.success(request, "Mahsulot sevimlilardan o'chirildi!")
    return redirect('view_wishlist')

@login_required
def view_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    return render(request, 'shop/wishlist.html', {'wishlist': wishlist})

@login_required
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Fikringiz qo'shildi!")
            return redirect('product_detail', slug=product.slug)
    return render(request, 'shop/add_review.html', {'product': product})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        coupon_code = request.POST.get('coupon_code')

        total_price = cart.get_total()
        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    active=True,
                    valid_from__lte=timezone.now(),
                    valid_to__gte=timezone.now()
                )
                # Chegirma hisoblashda Decimal ga aylantirish
                discount = Decimal(str(1 - coupon.discount_percent / 100))
                total_price = total_price * discount
            except Coupon.DoesNotExist:
                messages.error(request, "Noto'g'ri yoki yaroqsiz kupon kodi!")

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            total_price=total_price,
            coupon=coupon
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.get_price()
            )

        cart.items.all().delete()
        messages.success(request, "Buyurtma muvaffaqiyatli yaratildi!")
        return redirect('product_list')

    return render(request, 'shop/checkout.html', {'cart': cart})