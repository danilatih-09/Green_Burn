from  django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Product, Category, Manufacturer, Cart, CartItem, Order, OrderItem
from .forms import RegisterForm, EmailChangeForm
from django.views.decorators.csrf import ensure_csrf_cookie

from django.core.mail import send_mail 
from openpyxl import Workbook
import random
import json
from datetime import datetime

from rest_framework import viewsets, generics, permissions
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    ManufacturerSerializer,
    CartSerializer,
    CartItemSerializer,
    ProfileSerializer,
    OrderSerializer,
)
from .permissions import IsAdminRoleOrReadOnly


# сопоставление "название категории -> файл картинки" для плиток на главной.
# привязка по id ненадёжна (id в БД зависит от порядка создания в populate.py
# и не совпадает с тем, как пронумерованы файлы 1-12 в static/images),
# поэтому сопоставляем по названию категории, которое стабильно
CATEGORY_IMAGE_MAP = {
    "Искусственные цветы": "1.jpg",
    "Вазы и кашпо": "2.jpg",
    "Сувениры и декор": "3.jpg",
    "Горшки для цветов": "4.jpg",
    "Изделия из дерева": "5.jpg",
    "Корзины плетёные": "6.jpg",
    "Удобрение и бытовая химия": "7.jpg",
    "Товары для дома": "8.jpg",
    "Упаковка для цветов": "9.jpg",
    "Флористические материалы": "10.jpg",
    "Барбекю/Кемпинг": "11.jpg",
    "Спортивные товары": "12.png",
}


@ensure_csrf_cookie  # гарантирует cookie csrftoken с первого визита на сайт —
# без этого декоратора cookie появлялся только "случайно", если на странице
# рендерилась хотя бы одна форма с {% csrf_token %} (например форма логаута в base.html
# для залогиненных). Для анонимного посетителя без этого декоратора cookie мог
# не появиться вообще, и fetch с каталога не находил бы токен через getCsrfToken()
def home(request):
    """Главная страница"""
    products = Product.objects.all()[:4]  # Показываем первые 6 товаров
    # добавил категории в контекст, чтобы на главной можно было вывести плитки категорий
    categories = list(Category.objects.all())

    # подмешиваем каждой категории имя файла картинки (по названию),
    # чтобы в шаблоне просто писать {{ category.image_filename }}
    for category in categories:
        category.image_filename = CATEGORY_IMAGE_MAP.get(category.name)

    context = {
        'products': products,
        'categories': categories,
    }
    
    return render(request, 'shop/home.html', context)

# регистрация: создаёт User + автоматически Profile (через сигнал в models.py),
# затем сразу логинит пользователя, чтобы не заставлять его входить второй раз
def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('account')
    else:
        form = RegisterForm()

    return render(request, 'shop/register.html', {'form': form})


# вход через стандартный Django LoginView — он уже умеет показывать ошибки
# ("неверный логин/пароль"), защищён от CSRF и редиректит после входа.
# Свой шаблон template_name переопределяет дефолтный регистрационный экран Django
class CustomLoginView(LoginView):
    template_name = 'shop/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # после входа ведём в личный кабинет, а не на страницу логина
        return reverse_lazy('account')


# выход через стандартный LogoutView — было /admin/logout/ (заглушка из админки),
# теперь обычный выход с возвратом на главную
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')


# личный кабинет — здесь будет полноценная реализация (профиль + заказы),
# пока минимальная версия, чтобы регистрация и вход куда-то вели
# личный кабинет: блок профиля (редактируется через fetch PATCH /api/me/, см. main.js)
# и блок "Мои заказы" — рендерится сразу через контекст, без отдельного fetch,
# чтобы страница показывала данные мгновенно, без дополнительного запроса при загрузке
@login_required(login_url='/login/')
def account(request):
    profile = request.user.profile
    orders = request.user.orders.prefetch_related('items').all()
    categories = Category.objects.all()  # для выпадающего списка "любимая категория"

    context = {
        'profile': profile,
        'orders': orders,
        'categories': categories,
    }
    return render(request, 'shop/account.html', context)

# страница "Настройки": две независимые формы на одной странице —
# смена пароля и смена email. У каждой формы своё скрытое поле-маркер
# в HTML (name="change_password" / name="change_email" у кнопки submit),
# по нему view понимает, какую именно форму отправили.
@login_required(login_url='/login/')
def account_settings(request):
    # пустые формы для обычного открытия страницы (GET-запрос)
    password_form = PasswordChangeForm(user=request.user)
    email_form = EmailChangeForm(user=request.user, initial={'email': request.user.email})

    if request.method == 'POST':
        # 'change_password' in request.POST — сработает, если в отправленных
        # данных есть кнопка с name="change_password", то есть нажали
        # именно кнопку "Сохранить пароль"
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()  # тут пароль реально меняется в базе
                # обновляем сессию новым хэшем пароля, чтобы не выкинуло из аккаунта
                update_session_auth_hash(request, user)
                # редирект после успешного POST (Post/Redirect/Get),
                # чтобы при обновлении страницы форма не отправлялась повторно
                return redirect('account_settings')

        elif 'change_email' in request.POST:
            email_form = EmailChangeForm(user=request.user, data=request.POST)
            if email_form.is_valid():
                email_form.save()
                return redirect('account_settings')

    context = {
        'password_form': password_form,
        'email_form': email_form,
    }
    return render(request, 'shop/settings.html', context)

# страница одной заказа — кнопка "Подробнее" в личном кабинете
@login_required(login_url='/login/')
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    # тот же принцип, что и в cart_view: чужой заказ открыть нельзя,
    # кроме случая когда смотрит сам администратор
    is_admin = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.role == request.user.profile.ROLE_ADMIN
    )
    if order.user != request.user and not is_admin:
        return redirect('account')

    return render(request, 'shop/order_detail.html', {'order': order})


def about(request):
    return render (request,'shop/about.html' )

def author(request):
  return render(request, 'shop/author.html')

# каталог (список товаров)
def product_list(request):
   #Получаем все товары 
   products = Product.objects.all()

   # Получаем параметры из запроса
   category_id = request.GET.get('category')
   manufacturer_id = request.GET.get('manufacturer')
   search_query = request.GET.get('search', '')

  # Фильтр 
   if category_id:
      products = products.filter(category_id = category_id)

   if manufacturer_id:
      products = products.filter(manufacturer_id = manufacturer_id)

  #Поиск по названию или описанию (Q-объекты для ИЛИ)
   if search_query:
      products = products.filter(
         Q(name__icontains=search_query) | 
         Q(description__icontains=search_query)
      )
  # ПОлучаем все категрии и производитеелй для выпадающих спиосков 
   manufacturers = Manufacturer.objects.all()
   categories = Category.objects.all()

   # добавил пагинацию: по 9 товаров на страницу
   paginator = Paginator(products, 9)
   page_number = request.GET.get('page')
   page_obj = paginator.get_page(page_number)

   # Контекст для шаблона 
   context = {
      'products': products,
      'categories': categories,
      'manufacturers': manufacturers,
      'selected_categories': category_id,
      'selected_manufacturers': manufacturer_id,
      'search_query': search_query,
  }
   
  # render - функция которя собирает данные и преоброзует в HTML шаблон 
   return render(request, 'shop/product_list.html', context)

def product_detail(request, pk):
    """Детальная информация о товаре , pk - первичный ключ (ID) товара из URL """

    # get_object_or_404 вернёт товар или ошибку 404 если не найден
    product = get_object_or_404(Product, pk=pk)
    
    context = {
        'product': product,
    }
    
    return render(request, 'shop/product_detail.html', context)  

#ограничения доступа к корзине.
@login_required(login_url='/login/')
def add_to_cart(request, product_id):
   #  Добавление товара в корзину 
   product = get_object_or_404(Product, id = product_id)

   # Получаем корзину пользователя (или создаём новую)
   cart, created = Cart.objects.get_or_create(user=request.user)

   # Проверяем, есть ли товар уже в корзине
   cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantities': 1} 
    )
    
   if not created:
        # Товар уже есть - увеличиваем количество
        cart_item.quantities += 1
   else:
        cart_item.quantities = 1
    
    # Валидация: не больше чем на складе
   if cart_item.quantities > product.quantities_stock:
        cart_item.quantities = product.quantities_stock
    
   cart_item.save()
    
    # Перенаправляем на страницу корзины
   return redirect('cart_view')

# новый эндпоинт специально для JS (main.js): принимает JSON, отдаёт JSON,
# чтобы добавление в корзину можно было делать через fetch без перезагрузки страницы
@login_required(login_url='/login/')
@require_POST
def api_add_to_cart(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Некорректный JSON'}, status=400)
 
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)
 
    if not product_id:
        return JsonResponse({'ok': False, 'error': 'Не указан product_id'}, status=400)
 
    product = get_object_or_404(Product, id=product_id)
 
    if product.quantities_stock <= 0:
        return JsonResponse({'ok': False, 'error': 'Товара нет в наличии'}, status=400)
 
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantities': 0}
    )
 
    # не даём добавить больше, чем есть на складе
    cart_item.quantities = min(cart_item.quantities + quantity, product.quantities_stock)
    cart_item.save()
 
    return JsonResponse({
        'ok': True,
        'message': f'«{product.name}» добавлен в корзину',
        'cart_count': cart.items.count(),
        'item_quantity': cart_item.quantities,
    })

@login_required(login_url='/login/')
def update_cart(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id = item_id)

    # Проверка принадлежит ли корзина данному пользователю 
    if cart_item.cart.user != request.user:
        return redirect('product_list')
    
    if request.method == 'POST':
        # Получаем новое количество из формы
        new_quantity = int(request.POST.get('quantity', 1))
        
        # Валидация: не больше чем на складе
        if new_quantity > cart_item.product.quantities_stock:
            new_quantity = cart_item.product.quantities_stock
        
        if new_quantity > 0:
            cart_item.quantities = new_quantity
            cart_item.save()
        else:
            # Если 0 или меньше - удаляем
            cart_item.delete()
    
    return redirect('cart_view')

@login_required(login_url='/login/')
def remove_from_cart(request, item_id):
    # удаление их корзины 
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Проверка: корзина принадлежит текущему пользователю
    if cart_item.cart.user != request.user:
        return redirect('product_list')
    
    cart_item.delete()
    
    return redirect('cart_view')

@login_required(login_url='/login/')
def cart_view(request):
    """Просмотр корзины пользователя"""
    # Получаем корзину пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Получаем все элементы корзины
    cart_items = cart.items.all()
    
    # Вычисляем общую стоимость
    total_cost = sum(item.item_cost() for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_cost': total_cost,
    }
    
    return render(request, 'shop/cart.html', context)


# Оформление заказа

# было @login_required без login_url — при анонимном доступе редиректило на
# несуществующий /accounts/login/ (404), теперь ведёт на админский логин, как остальные cart-функции
@login_required(login_url='/login/')
def checkout(request):
    message = ""
    order_number = None  # если заказ успешно оформлен, сюда попадёт его номер —
    # по этому флагу шаблон решает, показывать форму или экран "Заказ оформлен"
    if request.method == "POST":
        # Берем данные из формы
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
 
        if not all([first_name, last_name, email, address]):
            message = "Пожалуйста, заполните все поля."
        else:
            # генерация номера заказа
            order_number = random.randint(100000, 999999)

            # дата и время заказа
            order_date = datetime.now()

            # сохраняем заказ в базу — раньше checkout() только генерировал Excel-файл
            # и ничего не записывал в БД, поэтому "Мои заказы" и /api/orders/ были бы
            # навсегда пустыми, даже если человек реально оформил покупку
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = list(cart.items.select_related('product').all())
            total_cost = sum(item.item_cost() for item in cart_items)

            order = Order.objects.create(
                user=request.user,
                order_number=str(order_number),
                first_name=first_name,
                last_name=last_name,
                email=email,
                address=address,
                total_cost=total_cost,
            )

            # OrderItem хранит снимок цены/названия на момент покупки (см. models.py)
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantities,
                )

            # после оформления заказа корзина очищается — иначе те же товары
            # остались бы в корзине и человек мог бы "оформить" их повторно
            cart.items.all().delete()

            # создаем Excel файл
            workbook = Workbook()
            sheet = workbook.active

            sheet["A1"] = "Чек заказа"
            sheet["A3"] = "Номер заказа:"
            sheet["B3"] = order_number

            sheet["A4"] = "Покупатель:"
            sheet["B4"] = f"{first_name} {last_name}"

            sheet["A5"] = "Email:"
            sheet["B5"] = email

            sheet["A6"] = "Адрес доставки:"
            sheet["B6"] = address

            sheet["A7"] = "Дата заказа:"
            sheet["B7"] = order_date.strftime("%d-%m-%Y %H:%M")

            filename = f"order_{order_number}.xlsx"
            workbook.save(filename)

            # отправка письма на email из формы
            # обернул в try/except: если SMTP не настроен (EMAIL_HOST_USER пустой),
            # раньше вся страница падала с ошибкой вместо показа сообщения об заказе
            try:
                send_mail(
                    "Ваш заказ оформлен",
                    f"Спасибо за покупку! Номер вашего заказа: {order_number}",
                    settings.EMAIL_HOST_USER,  # от кого
                    [email],             # кому
                    fail_silently=True,
                )
            except Exception:
                pass

            message = f"Заказ {order_number} оформлен! Чек создан."
 
    return render(request, "shop/checkout.html", {"message": message, "order_number": order_number})

class ProductViewSet(viewsets.ModelViewSet):
 #ViewSet в Django REST Framework — это класс, который создаёт API для модели.
#Он автоматически делает основные операции с данными:
#получить список (GET)
#получить один объект (GET id)
#создать (POST)
#обновить (PUT/PATCH)
#удалить (DELETE)
    queryset = Product.objects.all() #queryset — это данные из базы данных, с которыми будет работать API. То есть получить все данные
    serializer_class = ProductSerializer #Serializer нужен чтобы преобразовать модель → JSON.
    # было IsAuthenticatedOrReadOnly (из settings) — любой залогиненный покупатель
    # мог создать/удалить товар. Теперь писать может только роль ADMIN
    permission_classes = [IsAdminRoleOrReadOnly]

#Создай API для модели Product, бери данные из базы, используй ProductSerializer для JSON.

class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class =  ManufacturerSerializer
    permission_classes = [IsAdminRoleOrReadOnly]  # тот же принцип: каталог производителей читают все, меняет только админ

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    # было queryset = Cart.objects.all() — любой залогиненный пользователь видел
    # ЧУЖИЕ корзины через /api/carts/. Теперь возвращаем только корзину текущего юзера
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Cart.objects.all()
        return Cart.objects.filter(user=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    # та же проблема, что и в CartViewSet — ограничиваем элементы корзины владельцем
    def get_queryset(self):
        if self.request.user.is_superuser:
            return CartItem.objects.all()
        return CartItem.objects.filter(cart__user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset =  Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminRoleOrReadOnly]  # категории тоже редактирует только админ


# заказы: GET /api/orders/ — пользователь видит только свои, администратор — все.
# создавать новый заказ через этот ViewSet не нужно (заказ создаётся через
# обычный checkout()), поэтому здесь нет отдельного permission на запись —
# хватает обычного IsAuthenticated, а видимость отдаёт get_queryset
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.role == user.profile.ROLE_ADMIN):
            return Order.objects.all()
        return Order.objects.filter(user=user)


# GET /api/me/ — профиль текущего пользователя, PATCH /api/me/ — его редактирование.
# RetrieveUpdateAPIView сразу даёт оба метода без лишнего кода
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']  # PUT не нужен — профиль редактируется частично

    def get_object(self):
        # объект всегда профиль самого запрашивающего — get_object_or_404 по id не нужен,
        # иначе можно было бы передать чужой id в URL и читать/менять чужой профиль
        return self.request.user.profile