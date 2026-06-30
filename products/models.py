from django.urls import reverse
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image=models.ImageField(upload_to="categories/")
    def get_absolute_url(self):
        return reverse("products:products", kwargs={"pk": self.pk})
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0
    )

    image_url = models.URLField(max_length=1000)

    image_path = models.CharField(max_length=500, blank=True)
    
    product_url = models.URLField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

