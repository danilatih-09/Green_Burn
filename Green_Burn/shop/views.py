from  django.http import HttpResponse 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Product, Category, Manufacturer, Cart, CartItem

from django.core.mail import send_mail 
from openpyxl import Workbook
import random
from datetime import datetime


def home(request):
    """Главная страница"""
    products = Product.objects.all()[:6]  # Показываем первые 6 товаров
    
    context = {
        'products': products,
    }
    
    return render(request, 'shop/home.html', context)

def about(request):
    return HttpResponse ("""
  О магазине Green Burn:
  🌿 Green Burn — флористика и сувениры с душой
  Мы — минский магазин для тех, кто создаёт красоту. В Green Burn вы найдёте всё для флористики: горшки, кашпо, ленты, пленку, сухоцветы, упаковку и материалы от проверенных брендов. А ещё — тёплые, продуманные сувениры: шкатулки, фоторамки, подсвечники, интерьерные часы и подарки на любой повод.
✅ Прямые поставки — честные цены
✅ Доставка по всей Беларуси
✅ Опт для флористов, студий и бизнеса
✅ Только качественные и эстетичные товары
  Большинство наших клиентов возвращаются снова — потому что здесь легко найти то, что вдохновляет.
🌱 Green Burn — где растёт хорошее настроение.
    """)

def author(request):
  return HttpResponse ("""
  Меня зовут Данила Тихонович, и я — создатель Green Burn.
  Этот магазин родился из любви к живым растениям, уюту и деталям, которые делают подарок по-настоящему личным. Я лично подбираю каждый товар — от флористических материалов до интерьерных сувениров — чтобы вы могли создавать, дарить и украшать с уверенностью и вдохновением.
  Green Burn — это не просто каталог. Это место, где встречаются красота, качество и забота. Спасибо, что вы с нами!
  """)

# каталог (список товаров)
def product_list(request):
   #Получаем все товары 
   products = Product.objects.all()

   # Получаем параметры из запроса
   category_id = request.GET.get('category')
   manufacturer_id = request.GET.get('manufacture')
   search_query = request.GET.get('search', '')

  # Фильтр 
   if category_id:
      products = products.filter(category_id = category_id)

   if manufacturer_id:
      products = products.filter(manufacturer_id = manufacturer_id)

  #Поиск по названию или описанию (Q-объекты для ИЛИ)
   if search_query:
      search_query = products.filter(
         Q(name__icontains=search_query) | 
         Q(description__icontains=search_query)
      )
  # ПОлучаем все категрии и производитеелй для выпадающих спиосков 
   manufacturers = Manufacturer.objects.all()
   categories = Category.objects.all()

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
@login_required(login_url='/admin/login/')
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

@login_required(login_url='/admin/login/')
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

@login_required(login_url='/admin/login/')
def remove_from_cart(request, item_id):
    # удаление их корзины 
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Проверка: корзина принадлежит текущему пользователю
    if cart_item.cart.user != request.user:
        return redirect('product_list')
    
    cart_item.delete()
    
    return redirect('cart_view')

@login_required(login_url='/admin/login/')
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

@login_required  # только зареганные пользователи 
def checkout(request):
    message = ""
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
            send_mail(
                "Ваш заказ оформлен",
                f"Спасибо за покупку! Номер вашего заказа: {order_number}",
                "shop@example.com",  # от кого
                [email],             # кому
                fail_silently=False,
            )

            message = f"Заказ {order_number} оформлен! Чек создан."

    return render(request, "shop/checkout.html", {"message": message})