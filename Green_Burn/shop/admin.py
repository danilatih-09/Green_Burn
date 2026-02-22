from django.contrib import admin
from .models import Manufacturer, Category, Product, Cart, CartItem


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