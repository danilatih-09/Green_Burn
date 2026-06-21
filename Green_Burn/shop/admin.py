from django.contrib import admin
from .models import Manufacturer, Category, Product, Cart, CartItem, Profile, Order, OrderItem


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'description')  
    search_fields = ('name', 'country')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')  
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantities_stock', 'category', 'manufacturer', 'photo','description')
    list_filter = ('category', 'manufacturer')
    search_fields = ('name', 'category')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    #readonly_fields - поле которое нельзя изменять 
    readonly_fields = ('created_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantities')
    list_filter = ('cart',)


# регистрация Profile в админке — нужно, чтобы можно было вручную назначить
# роль ADMIN/MANAGER пользователю через стандартную админку Django
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'delivery_city', 'favorite_category')
    list_filter = ('role',)
    search_fields = ('user__username', 'full_name', 'phone')


# для заказов отдельно показываем позиции заказа прямо на странице заказа (inline),
# чтобы не открывать каждую позицию отдельно
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_cost', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_number', 'user__username', 'email')
    readonly_fields = ('order_number', 'user', 'created_at')
    inlines = [OrderItemInline]