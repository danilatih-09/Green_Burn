import os
import django
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Green_Burn.settings')
django.setup()

from django.contrib.auth.models import User
from shop.models import Manufacturer, Category, Product, Cart, CartItem


def populate():

    # ОЧИСТКА БАЗЫ
    print("\n🗑️  Очистка старых данных...")
    CartItem.objects.all().delete()
    Cart.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Manufacturer.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    print(" База очищена")

    # СОЗДАНИЕ ПРОИЗВОДИТЕЛЕЙ (6 шт)
    print("\nСоздание 6 производителей...")
    manufacturers_data = [
        {"name": "Следопыт", "country": "Россия", "description": "Туристическое снаряжение и барбекю"},
        {"name": "Гера", "country": "Россия", "description": "Удобрения и грунты"},
        {"name": "Hendriks Greenhouses", "country": "Нидерланды", "description": "Растения и цветочная продукция"},
        {"name": "Guangdong Jiangmen Green Deco", "country": "Китай", "description": "Товары для декора"},
        {"name": "Jacobson Floral Supply", "country": "США", "description": "Флористические материалы"},
        {"name": "Xiamen Greendeco", "country": "Китай", "description": "Искусственные растения"},
    ]
    
    manufacturers = []
    for data in manufacturers_data:
        m = Manufacturer.objects.create(**data)
        manufacturers.append(m)
        print(f"   ✓ {m.name}")
    print(f"Создано производителей: {len(manufacturers)}")

    # СОЗДАНИЕ КАТЕГОРИЙ (11 шт)
    print("\n📦 Создание 11 категорий...")
    categories_data = [
        {"name": "Барбекю/Кемпинг", "description": "Товары для отдыха на природе"},
        {"name": "Флористические материалы", "description": "Материалы для цветов"},
        {"name": "Упаковка для цветов", "description": "Упаковочные материалы"},
        {"name": "Товары для дома", "description": "Декор и освещение"},
        {"name": "Удобрение и бытовая химия", "description": "Удобрения и защита"},
        {"name": "Корзины плетёные", "description": "Плетёные корзины"},
        {"name": "Изделия из дерева", "description": "Деревянный декор"},
        {"name": "Горшки для цветов", "description": "Горшки и кашпо"},
        {"name": "Сувениры и декор", "description": "Декоративные изделия"},
        {"name": "Вазы и кашпо", "description": "Вазы"},
        {"name": "Искусственные цветы", "description": "Искусственные растения"},
    ]
    
    categories = []
    for data in categories_data:
        c = Category.objects.create(**data)
        categories.append(c)
        print(f"   ✓ {c.name}")
    print(f"Создано категорий: {len(categories)}")

    # СОЗДАНИЕ ТОВАРОВ (34 шт)
    print("\nСоздание 34 товаров...")
    
    products_data = [
        # Барбекю/Кемпинг - 3 товара
        {"name": "Мангал складной", "description": "Складной мангал", "price": Decimal("85.00"), "quantities_stock": 25, "category": categories[0], "manufacturer": manufacturers[0]},
        {"name": "Горелка газовая", "description": "Газовая горелка", "price": Decimal("45.00"), "quantities_stock": 40, "category": categories[0], "manufacturer": manufacturers[0]},
        {"name": "Набор для барбекю", "description": "Набор 5 предметов", "price": Decimal("65.00"), "quantities_stock": 30, "category": categories[0], "manufacturer": manufacturers[0]},
        
        # Флористические материалы - 3 товара
        {"name": "Флористическая губка", "description": "Оазис 23x11x7 см", "price": Decimal("15.00"), "quantities_stock": 100, "category": categories[1], "manufacturer": manufacturers[4]},
        {"name": "Проволока флористическая", "description": "0.8 мм 20м", "price": Decimal("12.00"), "quantities_stock": 80, "category": categories[1], "manufacturer": manufacturers[4]},
        {"name": "Лента атласная", "description": "50 мм 10м", "price": Decimal("10.00"), "quantities_stock": 150, "category": categories[1], "manufacturer": manufacturers[4]},
        
        # Упаковка - 3 товара
        {"name": "Бумага крафт", "description": "50 листов", "price": Decimal("22.00"), "quantities_stock": 60, "category": categories[2], "manufacturer": manufacturers[4]},
        {"name": "Пакеты прозрачные", "description": "100 шт", "price": Decimal("14.00"), "quantities_stock": 70, "category": categories[2], "manufacturer": manufacturers[4]},
        {"name": "Коробка подарочная", "description": "20x20x10 см", "price": Decimal("6.50"), "quantities_stock": 200, "category": categories[2], "manufacturer": manufacturers[4]},
        
        # Товары для дома - 3 товара
        {"name": "Светильник LED Цветок", "description": "Декоративный", "price": Decimal("55.00"), "quantities_stock": 35, "category": categories[3], "manufacturer": manufacturers[3]},
        {"name": "Гирлянда светодиодная", "description": "10 м", "price": Decimal("32.00"), "quantities_stock": 50, "category": categories[3], "manufacturer": manufacturers[3]},
        {"name": "Светильник Бамбук", "description": "Настольный", "price": Decimal("75.00"), "quantities_stock": 25, "category": categories[3], "manufacturer": manufacturers[3]},
        
        # Удобрения - 3 товара
        {"name": "Удобрение Цветочное", "description": "500 г", "price": Decimal("10.00"), "quantities_stock": 100, "category": categories[4], "manufacturer": manufacturers[1]},
        {"name": "Грунт Цветочный", "description": "5 л", "price": Decimal("6.50"), "quantities_stock": 150, "category": categories[4], "manufacturer": manufacturers[1]},
        {"name": "Средство Антислизень", "description": "100 г", "price": Decimal("5.50"), "quantities_stock": 80, "category": categories[4], "manufacturer": manufacturers[1]},
        
        # Корзины - 3 товара
        {"name": "Корзина круглая", "description": "30 см", "price": Decimal("45.00"), "quantities_stock": 40, "category": categories[5], "manufacturer": manufacturers[2]},
        {"name": "Корзина овальная", "description": "40 см", "price": Decimal("58.00"), "quantities_stock": 30, "category": categories[5], "manufacturer": manufacturers[2]},
        {"name": "Набор корзин", "description": "3 шт", "price": Decimal("85.00"), "quantities_stock": 20, "category": categories[5], "manufacturer": manufacturers[2]},
        
        # Изделия из дерева - 3 товара
        {"name": "Кашпо подвесное", "description": "Деревянное", "price": Decimal("32.00"), "quantities_stock": 45, "category": categories[6], "manufacturer": manufacturers[5]},
        {"name": "Ящик деревянный", "description": "25 см", "price": Decimal("42.00"), "quantities_stock": 35, "category": categories[6], "manufacturer": manufacturers[5]},
        {"name": "Подставка 3 яруса", "description": "Деревянная", "price": Decimal("98.00"), "quantities_stock": 15, "category": categories[6], "manufacturer": manufacturers[5]},
        
        # Горшки - 3 товара
        {"name": "Горшок керамический", "description": "15 см белый", "price": Decimal("16.00"), "quantities_stock": 100, "category": categories[7], "manufacturer": manufacturers[2]},
        {"name": "Горшок пластиковый", "description": "20 см", "price": Decimal("10.00"), "quantities_stock": 150, "category": categories[7], "manufacturer": manufacturers[2]},
        {"name": "Горшок глиняный", "description": "18 см", "price": Decimal("11.50"), "quantities_stock": 120, "category": categories[7], "manufacturer": manufacturers[2]},
        
        # Сувениры - 3 товара
        {"name": "Статуэтка Птица", "description": "20 см", "price": Decimal("28.00"), "quantities_stock": 50, "category": categories[8], "manufacturer": manufacturers[3]},
        {"name": "Панно Цветы", "description": "30x30 см", "price": Decimal("45.00"), "quantities_stock": 40, "category": categories[8], "manufacturer": manufacturers[3]},
        {"name": "Свечи ароматические", "description": "набор 3 шт", "price": Decimal("23.00"), "quantities_stock": 60, "category": categories[8], "manufacturer": manufacturers[3]},
        
        # Вазы - 3 товара
        {"name": "Ваза стеклянная", "description": "30 см", "price": Decimal("32.00"), "quantities_stock": 45, "category": categories[9], "manufacturer": manufacturers[5]},
        {"name": "Кашпо с узором", "description": "25 см", "price": Decimal("42.00"), "quantities_stock": 35, "category": categories[9], "manufacturer": manufacturers[5]},
        {"name": "Ваза напольная", "description": "60 см", "price": Decimal("118.00"), "quantities_stock": 10, "category": categories[9], "manufacturer": manufacturers[5]},
        
        # Искусственные цветы - 4 товара
        {"name": "Роза искусственная", "description": "70 см", "price": Decimal("21.00"), "quantities_stock": 80, "category": categories[10], "manufacturer": manufacturers[5]},
        {"name": "Орхидея в горшке", "description": "40 см", "price": Decimal("45.00"), "quantities_stock": 50, "category": categories[10], "manufacturer": manufacturers[5]},
        {"name": "Фикус искусственный", "description": "80 см", "price": Decimal("75.00"), "quantities_stock": 30, "category": categories[10], "manufacturer": manufacturers[5]},
        {"name": "Букет полевые цветы", "description": "Искусственный", "price": Decimal("28.00"), "quantities_stock": 60, "category": categories[10], "manufacturer": manufacturers[5]},
    ]
    
    products = []
    for data in products_data:
        p = Product.objects.create(**data)
        products.append(p)
    print(f"Создано товаров: {len(products)}")

    # СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ (5 шт)
    print("\n📦 Создание 5 пользователей с корзинами...")
    users_data = [
        {"username": "user1", "email": "user1@example.com", "password": "pass1"},
        {"username": "user2", "email": "user2@example.com", "password": "pass2"},
        {"username": "user3", "email": "user3@example.com", "password": "pass3"},
        {"username": "user4", "email": "user4@example.com", "password": "pass4"},
        {"username": "user5", "email": "user5@example.com", "password": "pass5"},
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={"email": user_data["email"], "is_active": True}
        )
        if created:
            user.set_password(user_data["password"])
            user.save()
        
        cart, _ = Cart.objects.get_or_create(user=user)
        
        num_items = random.randint(2, 3)
        selected_products = random.sample(products, num_items)
        
        for product in selected_products:
            CartItem.objects.create(cart=cart, product=product, quantities=random.randint(1, 3))
        
        print(f" {user.username}: корзина с {num_items} товарами")
    print(f"Создано пользователей: {len(users_data)}")

    # ИТОГИ
    print(f"Производителей: {Manufacturer.objects.count()}")
    print(f"Категорий: {Category.objects.count()}")
    print(f"Товаров: {Product.objects.count()}")
    print(f"Пользователей: {User.objects.filter(is_superuser=False).count()}")
    print(f"Корзин: {Cart.objects.count()}")


if __name__ == "__main__":
    populate()