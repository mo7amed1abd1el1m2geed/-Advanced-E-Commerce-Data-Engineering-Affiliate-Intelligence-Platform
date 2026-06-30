from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Category
from django.db.models import Q
from .models import Category, Product

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

    return render(
        request,
        "products/product.html",
        {"product": product},
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
