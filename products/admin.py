from django.contrib import admin
from .models import Category, Product
admin.site.register(Category)
admin.site.register(Product)
admin.site.site_header='Site Admin'
