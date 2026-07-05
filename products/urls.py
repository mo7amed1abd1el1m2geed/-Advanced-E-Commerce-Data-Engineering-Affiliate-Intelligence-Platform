from django.urls import path
from . import views

urlpatterns = [
    path("", views.categories, name="categories"),

    path("category/<int:pk>/", views.products, name="products"),
    
    path("product/<int:pk>/", views.product, name="product"),
    path("cart/",views.cart_view,name="cart_view"),
    path("/add_to_cart/<int:pk>/",views.add_to_cart,name="add_to_cart"),
    path("/remove_from_cart/<int:pk>/",views.remove_from_cart,name="remove_from_cart"),
    path("/increase_one/<int:pk>/",views.increase_one,name="increase_one"),
    path("/decrease_one/<int:pk>/",views.decrease_one,name="decrease_one"),
]