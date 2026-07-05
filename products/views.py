from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from .models import Category
from django.db.models import Q
from .models import Category, Product
from .models import Cart,CartItem
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

def categories(request):
    search = request.GET.get("search", "")

    categories = Category.objects.all()

    if search:
        categories = categories.filter(
            name__icontains=search
        )
       

    return render(
        request,
        "products/categories.html",
        {
            "categories": categories,
            "search": search,
        },
    )


def product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = get_cart(request)
    cart_item = cart.items.filter(product=product).first()

    return render(
        request,
        "products/product.html",
        {"product": product,"cart_item":cart_item},
    )



def products(request, pk):
    category = get_object_or_404(Category, pk=pk)

    search = request.GET.get("search", "")

    products = Product.objects.filter(category=category)

    if search:
        products = products.filter(
            name__icontains=search
        )

    paginator = Paginator(products, 8)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "products/products.html",
        {
            "category": category,
            "page_obj": page_obj,
            "search": search,
        },
    )


def get_cart(request):
    cart,created=Cart.objects.get_or_create(user=request.user)
    return cart


@login_required
def cart_view(request):
    cart=get_cart(request)
    items=cart.items.all()
    context={
        "items":items
    }
    return render(request,"products/cart.html",context)

@login_required
@require_POST
def add_to_cart(request,pk):
    product=get_object_or_404(Product,pk=pk)
    cart=get_cart(request)
    cart_item,created=CartItem.objects.get_or_create(product=product,cart=cart)
    if not created:
        cart_item.quantity+=1
        cart_item.save()
    return  redirect(request.META.get("HTTP_REFERER", "/"))      

@login_required
@require_POST
def remove_from_cart(request,pk):
    cart=get_cart(request)
    cartitem=get_object_or_404(CartItem,pk=pk,cart=cart)
    cartitem.delete()
    return  redirect(request.META.get("HTTP_REFERER", "/"))    

@login_required
@require_POST
def increase_one(request,pk):
    cart=get_cart(request)
    cartitem=get_object_or_404(CartItem,pk=pk,cart=cart)
    cartitem.quantity+=1
    cartitem.save()
    return  redirect(request.META.get("HTTP_REFERER", "/"))    


@login_required
@require_POST
def decrease_one(request,pk):
    cart=get_cart(request)
    cart_item=get_object_or_404(CartItem,pk=pk,cart=cart)
    if cart_item.quantity>1:
        cart_item.quantity-=1
        cart_item.save()
    else:        
        cart_item.delete()
    return redirect(request.META.get("HTTP_REFERER", "/"))   

