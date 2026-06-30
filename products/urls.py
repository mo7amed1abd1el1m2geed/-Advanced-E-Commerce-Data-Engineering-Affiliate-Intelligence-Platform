from django.urls import path
from . import views

urlpatterns = [
    path("", views.categories, name="categories"),

    path("category/<int:pk>/", views.products, name="products"),
    
    path("product/<int:pk>/", views.product, name="product"),
]