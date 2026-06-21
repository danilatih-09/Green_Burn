from rest_framework import permissions


# IsAuthenticatedOrReadOnly (что было раньше) пускает писать в каталог ЛЮБОГО
# залогиненного пользователя — то есть обычный покупатель тоже мог бы создать
# или удалить товар через /api/products/. Этот класс уже проверяет роль:
# смотреть может кто угодно, а создавать/менять/удалять — только Profile.role == ADMIN
class IsAdminRoleOrReadOnly(permissions.BasePermission):
    # примечание для отчёта по тестированию (там, где методичка ожидает 401 для
    # неаутентифицированных запросов): DRF с SessionAuthentication возвращает 403,
    # а не 401, потому что 401 требует заголовок WWW-Authenticate (он есть только
    # у Basic/Token-аутентификации) — это штатное поведение библиотеки, не баг
    def has_permission(self, request, view):
        # GET/HEAD/OPTIONS разрешены всем (в том числе анонимам)
        if request.method in permissions.SAFE_METHODS:
            return True

        # для остальных методов (POST/PUT/PATCH/DELETE) нужен вход и роль ADMIN
        if not request.user or not request.user.is_authenticated:
            return False

        # superuser (например, главный админ Django) тоже допускается —
        # на случай если роль в Profile не выставлена, а доступ нужен прямо сейчас
        if request.user.is_superuser:
            return True

        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.role == profile.ROLE_ADMIN


# для заказов: пользователь видит только свои; администратор — все.
# Используется внутри view (get_queryset), а не как permission_classes,
# потому что фильтрация по пользователю — это вопрос видимости данных,
# а не доступа к самому эндпоинту (доступ туда есть у любого залогиненного)
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == profile.ROLE_ADMIN:
            return True

        return obj.user == request.user