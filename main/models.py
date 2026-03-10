from django.db import models
from django.utils.text import slugify    # <- добавь эту строку

class Category(models.Model):
    name = models.CharField(max_length=120, verbose_name="Название категории")
    slug = models.SlugField(max_length=140, unique=True, blank=True, verbose_name="Slug для URL")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Фото категории")  # ← новое поле

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.slug:                    # если slug пустой — создаём автоматически
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, verbose_name="Название типа (ДШЛ, ТПМ и т.д.)")
    slug = models.SlugField(max_length=220, unique=True, blank=True, verbose_name="Slug для URL")
    description = models.TextField(verbose_name="Общее описание типа")
    main_image = models.ImageField(upload_to='products/main/', blank=True, null=True, verbose_name="Главное фото")
    second_image = models.ImageField(upload_to='products/second/', blank=True, null=True, verbose_name="Второе фото")
    video_url = models.URLField(blank=True, null=True, verbose_name="Видео YouTube")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")  # ← это поле
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тип шва"
        verbose_name_plural = "Типы швов"
        ordering = ['order', 'name']  # ← сортировка сначала по order, потом по имени

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Товар")
    message = models.TextField(blank=True, verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заявки")
    
    def __str__(self):
        return f"{self.name} — {self.phone}"
    
    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']
        
class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=120, verbose_name="Вариант / размер (ДШЛ-0/020, ДШЛ-15-УГЛ и т.д.)")
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="Цена от, ₸")
    size_a = models.CharField(max_length=60, blank=True, verbose_name="Размер A")
    size_b = models.CharField(max_length=60, blank=True, verbose_name="Размер B")
    size_c = models.CharField(max_length=60, blank=True, verbose_name="Размер C / высота")
    movement = models.CharField(max_length=80, blank=True, verbose_name="Перемещение, мм")
    load_mpa = models.CharField(max_length=60, blank=True, verbose_name="Нагрузка, МПа")
    compensator = models.CharField(max_length=120, blank=True, verbose_name="Компенсатор")
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Вариант"
        verbose_name_plural = "Варианты"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.product.name} — {self.name}"