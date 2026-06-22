from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    photo = models.ImageField(upload_to= 'products/',blank = True, null = True, verbose_name="Фото")
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
    quantities = models.PositiveIntegerField(default=1, verbose_name= "Количество")

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

# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# выбран вариант с полем role (а не is_staff/is_superuser и не Groups),
# потому что для личного кабинета нужно явно показывать роль на странице,
# а с Groups это сделать сложнее без доп. кода
class Profile(models.Model):
    ROLE_CUSTOMER = 'CUSTOMER'
    ROLE_ADMIN = 'ADMIN'
    ROLE_MANAGER = 'MANAGER'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Покупатель'),
        (ROLE_ADMIN, 'Администратор'),
        (ROLE_MANAGER, 'Менеджер'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER, verbose_name="Роль")

    full_name = models.CharField(max_length=150, blank=True, verbose_name="Полное имя")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Телефон")
    address = models.CharField(max_length=255, blank=True, verbose_name="Адрес доставки")

    # 2 поля под тематику магазина (флористика/декор) — индивидуальное задание
    favorite_category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fans', verbose_name="Любимая категория"
    )
    delivery_city = models.CharField(max_length=100, blank=True, verbose_name="Город доставки")

    def __str__(self):
        return f"Профиль {self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


# при создании нового User Django сам вызовет этот сигнал и создаст Profile —
# без этого пришлось бы создавать профиль вручную в каждом view регистрации
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # instance — это только что созданный User.
        # is_superuser = True у пользователей, созданных через createsuperuser.
        # Если это суперпользователь — сразу даём ему роль ADMIN,
        # иначе (обычная регистрация) — роль CUSTOMER (покупатель).
        # Раньше роль всегда была CUSTOMER, поэтому админ в личном кабинете
        # видел надпись "Покупатель".
        role = Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_CUSTOMER
        Profile.objects.create(user=instance, role=role)


# ЗАКАЗ
# раньше заказов в базе не было вообще: checkout() только генерировал Excel-файл
# и ничего не сохранял. Без модели Order нечего было бы показывать в "Моих заказах"
# и нечего возвращать в /api/orders/, поэтому модель добавлена с нуля
class Order(models.Model):
    STATUS_NEW = 'NEW'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_DONE = 'DONE'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_PROCESSING, 'В обработке'),
        (STATUS_DONE, 'Выполнен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Пользователь")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Номер заказа")

    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    address = models.CharField(max_length=255, verbose_name="Адрес доставки")

    total_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма заказа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    def __str__(self):
        return f"Заказ {self.order_number} ({self.user.username})"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderItem(models.Model):
    # снимок состава заказа на момент покупки — если потом товар удалят
    # или поменяют цену, в старом заказе всё равно останутся правильные данные
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Товар")
    product_name = models.CharField(max_length=200, verbose_name="Название товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена на момент покупки")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def item_cost(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"