from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<slug:slug>/', views.category_detail, name='category_detail'),   # ← новая
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),    # ← изменено на slug
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('apply/', views.leave_application, name='apply'),
]