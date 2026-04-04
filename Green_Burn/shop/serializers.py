from rest_framework import serializers
from .models import Product, Manufacturer, Cart, CartItem, Category

class ProductSerializer(serializers.ModelSerializer): #создаём класс серилизатор, который из model django преобразует в JSON а потом обратно только в нормалной форме
    class Meta: # специальзированный класс 
        model = Product # говорим из какой модели ему брать  
        fields = '_all_' # говорим что считываем все поля в модели 

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '_all_'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '_all_'

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model =CartItem
        fields='_all_'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '_all_'

