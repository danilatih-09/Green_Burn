from rest_framework import serializers
from .models import Product, Manufacturer, Cart, CartItem, Category, Profile, Order, OrderItem

# Category и Manufacturer перенесены выше ProductSerializer, потому что
# ProductSerializer теперь ссылается на них напрямую (см. ниже)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__' # было fields = '_all_' (одно подчёркивание) — Django падал с ошибкой на любой запрос к API

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__' # было '_all_'

class ProductSerializer(serializers.ModelSerializer): #создаём класс серилизатор, который из model django преобразует в JSON а потом обратно только в нормалной форме
    # category и manufacturer теперь отдаются вложенным объектом (name, country и т.д.),
    # а не просто id — чтобы JS в main.js мог сразу отрисовать карточку товара
    # без дополнительных запросов к /api/categories/ и /api/manufacturers/
    category = CategorySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(), source='manufacturer', write_only=True
    )

    class Meta: # специальзированный класс 
        model = Product # говорим из какой модели ему брать  
        fields = '__all__' # было '_all_'

class CartItemSerializer(serializers.ModelSerializer):
    # добавил вложенный product, чтобы в корзине сразу было название/цена/фото товара
    product = ProductSerializer(read_only=True)

    class Meta:
        model =CartItem
        fields='__all__' # было '_all_'

class CartSerializer(serializers.ModelSerializer):
    # items и total_cost добавлены, чтобы /api/carts/ сразу отдавал содержимое корзины и итоговую сумму
    items = CartItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = '__all__' # было '_all_'

    def get_total_cost(self, obj):
        return obj.total_cost()
    
# для /api/me/ — отдаём профиль + базовые поля User (username, email), которые
# физически лежат не в Profile, а в стандартной модели User
class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'username', 'email', 'role', 'role_display',
            'full_name', 'phone', 'address',
            'favorite_category', 'delivery_city',
        ]
        # role нельзя менять самому пользователю через PATCH /api/me/ —
        # иначе любой покупатель мог бы сам назначить себе роль ADMIN
        read_only_fields = ['role']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'username', 'first_name', 'last_name',
            'email', 'address', 'total_cost', 'status', 'created_at', 'items',
        ]
        # пользователь не должен сам через API менять номер заказа, сумму или
        # выставлять себе статус "Выполнен" — это поля только для чтения
        read_only_fields = ['order_number', 'total_cost', 'status', 'created_at']