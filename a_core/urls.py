from django.contrib import admin
from django.urls import path, include
from a_home.views import *
from django.conf.urls.static import static
from django.conf import settings
from a_users.views import profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home_view ,name='home' ),
    path('profile/',include('a_users.urls')),
    path('accounts/', include('allauth.urls')),
    path('@<username>/',profile_view , name='profile'),
    path("products/", include(("products.urls", "products"), namespace="products")),
]

urlpatterns +=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
