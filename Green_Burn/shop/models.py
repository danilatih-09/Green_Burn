from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Создания класса КАТЕГОРИЯ
class Category (models.Model):
    name =  models.CharField(max_length=100, verbose_name="Название")
    # blank - разрешает ли оставлять поле пустым и null - разрешает ли в БД пустым 
    # CharField - Используется для коротких текстов (названия, имена)   
    # TextField - Поле для длинного текста.
    description =  models.TextField(blank = True,null = True, verbose_name="Описание")

    def __str__(self):
        return self.name   # возвращает значение поля название.
    
    # для читабельности
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

# Создание класса ПРОИЗВОДИТЕЛЬ 
class Manufacturer(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    country = models.CharField(max_length=100, verbose_name="Страна производитель")
    description = models.TextField(blank=True, null=True, verbose_name= "Описание")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

# Создание класса ТОВАР
class Product (models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    #upload_to= 'products/' - сохранение фоток в папку 
    photo = models.ImageField(upload_to= 'products/',verbose_name="Фото")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена") # сколько до запятой и после
    quantities_stock = models.IntegerField(verbose_name="Количество на складе")
    # связь с классом категория, on_delete=models.CASCADE - если удалить категорию, удалятся все товары в ней 
    # | releted_name ='products'-  обратная связь: из категории можно получить все товары через category.products.all()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name ='products', verbose_name="Категория")
    manufacturer = models.ForeignKey(Manufacturer,on_delete=models.CASCADE, related_name ='products', verbose_name="Производитель")

    def __str__(self):
        return self.name
    
    #Добавить валидацию: цена и количество_на_складе не могут быть отрицательными
    def clean(self):
        if self.price < 0:
            raise ValidationError("Цена не может быть отрицательной!")
        if self.quantities_stock < 0:
            raise ValidationError("Количесвто товара не может быть отрицательным!")
        
    # Валидация     
    def save(self, *args, **kwargs):
        self.full_clean()        #Запускает валидацию (проверку clean)
        super().save(*args, **kwargs)  #Сохраняет в БД
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

# КОРЗИНА
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Корзина {self.user.username}"
    
    def total_cost(self):
        return sum(item.item_cost() for item in self.items.all())
    
    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

# ЭЛЕМЕНТ КОРЗИНЫ
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,related_name='items', verbose_name="Корзина")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantities = models.PositiveIntegerField(verbose_name= "Количество")

    def __str__(self):
        return f"{self.product.name} ({self.product.quantities_stock } шт)"

    def item_cost(self):
        return self.product.price * self.quantities
    
    def availability(self):
        if self.quantities > self.product.quantities_stock:
            raise ValidationError(f"Недостаточно товара на складе. В наличии: {self.product.quantities_stock}")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        