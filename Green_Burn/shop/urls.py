from django.urls import path, include 
from . import views

from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    CategoryViewSet,
    ManufacturerViewSet,
    CartViewSet,
    CartItemViewSet,
    OrderViewSet,
    MeView,
)

router = DefaultRouter() #Router — это автоматический генератор URL для API
router.register(r'products', ProductViewSet) #создать API путь /products/ и связать его с ProductViewSet
router.register(r'categories', CategoryViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')
router.register(r'orders', OrderViewSet, basename='order')  # GET /api/orders/ — список заказов (только свои, админ — все)


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('author/', views.author, name='author'),

    # регистрация и вход/выход — было /admin/login/ и /admin/logout/ как временная
    # заглушка, теперь свои страницы с собственным дизайном (base.html, тема и т.д.)
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('account/', views.account, name='account'),
    path('account/settings/', views.account_settings, name='account_settings'),
    path('account/orders/<int:pk>/', views.order_detail, name='order_detail'),

    path('catalog/', views.product_list, name='product_list'),
    path('catalog/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'), # было name='checkout ' с пробелом — из-за этого {% url 'checkout' %} не работал
    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'), # новый путь под fetch-запрос из main.js
    path('api/me/', MeView.as_view(), name='api_me'),  # GET/PATCH профиля текущего пользователя
    path('api/', include(router.urls)), #все маршруты router будут начинаться с /api/

]