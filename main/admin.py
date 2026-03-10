from django.contrib import admin
from .models import Category, Product, Variant, Application

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1  # сколько пустых строк показывать для добавления
    fields = ('name', 'price', 'size_a', 'size_b', 'size_c', 'movement', 'load_mpa', 'compensator', 'image', 'order')
    ordering = ['order']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'slug', 'created_at')  # ← добавили order в список
    list_filter = ('category',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [VariantInline]
    list_editable = ('order',)  # ← можно менять порядок прямо в списке!
    fields = ('category', 'name', 'slug', 'description', 'main_image', 'second_image', 'video_url', 'order')  # ← добавили order в форму

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'movement', 'load_mpa')
    list_filter = ('product',)
    search_fields = ('name', 'product__name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone')