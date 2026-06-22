// ===== Тема (светлая / тёмная) =====
// Тема хранится в localStorage браузера пользователя и применяется к <html data-theme="...">
(function initTheme() {
    const root = document.documentElement;
    const saved = localStorage.getItem('gb-theme');

    if (saved === 'light' || saved === 'dark') {
        root.setAttribute('data-theme', saved);
    } else {
        // если темы ещё не выбирали — подстраиваемся под системные настройки устройства
        const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
        root.setAttribute('data-theme', prefersLight ? 'light' : 'dark');
    }

    updateThemeIcon();
})();

function updateThemeIcon() {
    const icon = document.querySelector('.theme-toggle-icon');
    if (!icon) return;
    const theme = document.documentElement.getAttribute('data-theme');
    icon.textContent = theme === 'light' ? '☀️' : '🌙';
}

function toggleTheme() {
    const root = document.documentElement;
    const current = root.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem('gb-theme', next);
    updateThemeIcon();
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }
});


// ===== CSRF-токен Django для POST/PATCH/DELETE через fetch =====
// было: сначала искали <input name=csrfmiddlewaretoken> на странице, а cookie — только
// как запасной вариант. Но на страницах без форм (например /catalog/) такого input нет,
// и токен зависел от случайного наличия формы где-то ещё на странице (через base.html).
// Теперь сначала читаем cookie csrftoken (Django выставляет его на любой странице,
// где встретился хотя бы один {% csrf_token %} — это гарантировано тегом в base.html),
// а input — как запасной вариант
function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) return match[1];

    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenInput ? tokenInput.value : '';
}


// ===== Уведомления (toast) =====
function showToast(message, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type === 'error' ? 'error' : 'success'}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 250);
    }, 3000);
}

// toast с кнопкой "Войти" — используется при ошибках авторизации (401/403),
// не скрывается по таймеру, чтобы пользователь успел нажать кнопку
function showToastWithLogin(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast toast-error';
    toast.innerHTML = `<div>${message}</div>`;

    const loginBtn = document.createElement('a');
    loginBtn.href = '/login/';
    loginBtn.className = 'btn btn-sm';
    loginBtn.style.marginTop = '10px';
    loginBtn.style.display = 'inline-block';
    loginBtn.textContent = 'Войти';
    toast.appendChild(loginBtn);

    container.appendChild(toast);
}


// ===== Единая обёртка над fetch для всех запросов к /api/ =====
// раньше каждая функция (addToCart, handleProfileFormSubmit, ...) сама добавляла
// заголовок X-CSRFToken и сама проверяла response.status — в одном месте это было
// сделано (через response.status === 403), в другом не сделано вовсе. apiFetch
// делает это один раз: CSRF-токен подставляется автоматически для не-GET запросов,
// а 401/403 обрабатываются одинаково везде на сайте
function apiFetch(url, options) {
    options = options || {};
    const method = (options.method || 'GET').toUpperCase();

    const headers = Object.assign({}, options.headers || {});

    // CSRF нужен только для запросов, которые меняют данные — GET/HEAD/OPTIONS не требуют токена
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        headers['X-CSRFToken'] = getCsrfToken();
    }

    return fetch(url, Object.assign({}, options, { headers }))
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                showToastWithLogin('Сессия истекла или нет доступа. Войдите заново.');
                // бросаем специальную ошибку, чтобы вызывающий код мог отличить
                // "уже показали сообщение про авторизацию" от прочих сбоев
                const authError = new Error('auth');
                authError.isAuthError = true;
                throw authError;
            }
            return response;
        });
}

// оставлена для обратной совместимости и для мест, где нужен именно булевый
// результат проверки без автоматического fetch (например, внутри .then())
function handleAuthError(response) {
    if (response.status === 401 || response.status === 403) {
        showToastWithLogin('Сессия истекла или нет доступа. Войдите заново.');
        return true;
    }
    return false;
}


// ===== Добавление товара в корзину через fetch (POST + CSRF) =====
function addToCart(productId, quantity) {
    quantity = quantity || 1;

    apiFetch('/api/cart/add/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: quantity }),
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok && data.ok) {
                showToast(data.message, 'success');
            } else {
                showToast(data.error || 'Не удалось добавить товар в корзину', 'error');
            }
        })
        .catch(error => {
            // если error.isAuthError — сообщение уже показано внутри apiFetch, повторно не дублируем
            if (!error.isAuthError) {
                showToast(error.message || 'Ошибка соединения с сервером', 'error');
            }
        });
}


// ===== Динамическая загрузка товаров из API (для каталога) =====
// используется, если на странице есть контейнер #product-list с data-атрибутами фильтров
function renderProducts(products) {
    const container = document.getElementById('product-list');
    if (!container) return;

    if (!products.length) {
        container.innerHTML = '<div class="empty-state">Товары не найдены</div>';
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="col-md-4 mb-4">
            <div class="card h-100">
                <img src="${product.photo || ''}" class="card-img-top product-image" alt="${product.name}">
                <div class="card-body">
                    <h5 class="card-title">${product.name}</h5>
                    <p class="card-text product-price">${product.price} BYN</p>
                    <button class="btn btn-primary" onclick="addToCart(${product.id})">
                        В корзину
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function loadProductsFromApi(url) {
    const container = document.getElementById('product-list');
    if (!container) return;

    // спиннер на время загрузки
    container.innerHTML = '<div class="spinner"></div>';

    // GET-запрос на каталог — без CSRF (он не нужен для чтения), но если сессия
    // вдруг истекла и эндпоинт стал недоступен (403), apiFetch всё равно покажет сообщение
    apiFetch(url || '/api/products/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Сервер вернул ошибку ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            renderProducts(Array.isArray(data) ? data : data.results || []);
        })
        .catch(error => {
            if (!error.isAuthError) {
                container.innerHTML = '<div class="empty-state">Не удалось загрузить товары. Попробуйте обновить страницу.</div>';
                showToast('Ошибка загрузки товаров: ' + error.message, 'error');
            }
        });
}


// ===== Личный кабинет: сохранение профиля через PATCH /api/me/ =====
// вызывается из account.html при отправке формы #profile-form
function handleProfileFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const statusEl = document.getElementById('profile-save-status');
    const formData = new FormData(form);

    // favorite_category может быть пустой строкой ("Не выбрано") — для API
    // это означает null, а не строку "" (DRF PrimaryKeyRelatedField не принимает "")
    const favoriteCategory = formData.get('favorite_category');

    const payload = {
        full_name: formData.get('full_name'),
        phone: formData.get('phone'),
        address: formData.get('address'),
        delivery_city: formData.get('delivery_city'),
        favorite_category: favoriteCategory ? Number(favoriteCategory) : null,
    };

    if (statusEl) {
        statusEl.textContent = 'Сохранение...';
        statusEl.className = 'profile-save-status';
    }

    apiFetch('/api/me/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok) {
                showToast('Профиль обновлён', 'success');
                if (statusEl) {
                    statusEl.textContent = 'Сохранено ✓';
                    statusEl.className = 'profile-save-status profile-save-ok';
                }
            } else {
                // DRF при ошибке валидации возвращает объект {field: [сообщения]}
                const firstError = Object.values(data)[0];
                const message = Array.isArray(firstError) ? firstError[0] : 'Не удалось сохранить профиль';
                showToast(message, 'error');
                if (statusEl) {
                    statusEl.textContent = 'Ошибка';
                    statusEl.className = 'profile-save-status profile-save-error';
                }
            }
        })
        .catch(error => {
            if (!error.isAuthError) {
                showToast('Ошибка соединения с сервером', 'error');
            }
            if (statusEl) {
                statusEl.textContent = '';
            }
        });
}