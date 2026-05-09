# Промт: Telegram Mini App для VPN-бота

## Контекст задачи

У тебя есть Telegram-бот на Python (aiogram/python-telegram-bot), который управляет VPN через 3x-ui панели. Нужно сделать **Telegram Mini App** — красивый iOS-интерфейс прямо внутри Telegram для управления клиентами.

Рабочий прототип уже существует. Твоя задача — повторить эту архитектуру под конкретный бот.

---

## Что должно получиться (UX)

### Главный экран — список клиентов
- Список всех VPN-клиентов со всех серверов
- Сортировка: просроченные → предупреждение → активные
- Цвета карточек: красный (#e84c4c) = просрочен, жёлтый (#f5a623) = < 7 дней или трафик > 90%, зелёный (#3fc26a) = активен
- У онлайн-клиентов — зелёная точка на аватаре и текст "🟢 онлайн"
- "Последний раз в сети": сегодня / вчера / N дн. назад / N нед. назад (берётся из SQLite)
- Прогресс-бар трафика с цветом (зелёный/жёлтый/красный)
- Бейдж: "N дней" или "Истёк"
- Тап на карточку → открывается bottom sheet с деталями

### Bottom sheet клиента (ClientSheet)
- Имя, сервер, трафик, дата истечения
- Кнопка **Продлить**: snap-слайдеры срока (7д/1м/3м/6м/1г) и трафика (∞/1/100/300/500/1000 ГБ)
- После продления: результат по серверам (OK/FAIL), кнопка "Показать ссылки"
- Кнопка **Удалить** с подтверждением

### Bottom sheet создания (CreateSheet)
- Поле: имя клиента
- Выбор группы серверов (например: "4 сервера" или "Один сервер")
- Snap-слайдеры срока и трафика
- Превью параметров перед созданием
- Кнопка **Создать**
- Результат: статус по серверам + кнопка "скопировать сообщение клиенту" + кнопка "скопировать ссылку-подписку"

**Сообщение клиенту (копируется в буфер):**
```
👋 Привет, {ИМЯ}! Твой ВПН готов:

1️⃣ Установи Happ, Streisand или V2RayTun, если ещё нет

2️⃣ 👉 Нажми — ВПН добавится сам: http://ВАШ_СЕРВЕР/r/happ/{UUID}?name=ИМЯ_СЕТИ
```

---

## Стек

| Слой | Технология |
|------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS + @telegram-apps/telegram-ui |
| Backend | FastAPI (Python 3.11) |
| БД | aiosqlite — таблица last_seen (email, timestamp ms) |
| Деплой | Docker Compose |
| Nginx | proxy /api/ → :8001, / → :8088 |

---

## Структура файлов

```
miniapp/
  frontend/
    src/
      components/
        ClientList.tsx      — список + аккордеон
        ClientSheet.tsx     — детали клиента, продление, удаление
        CreateSheet.tsx     — форма создания
      types.ts              — типы Client, RenewRequest, RenewResponse
      api.ts                — fetch-обёртки для всех эндпоинтов
      index.css             — iOS glassmorphism + snap-slider стили
    package.json
    vite.config.ts
    Dockerfile
  backend/
    main.py                 — FastAPI, все эндпоинты
    requirements.txt
    Dockerfile
  docker-compose.miniapp.yml
  nginx.conf
```

---

## API эндпоинты (FastAPI)

```
GET  /health               — health check
GET  /clients              — все клиенты со всех серверов
POST /clients              — создать клиента
POST /clients/{uuid}/renew — продлить клиента
DELETE /clients/{uuid}     — удалить клиента
```

**Критически важно:** при продлении и удалении — искать клиента по UUID во **ВСЕХ** inbound'ах **ВСЕХ** серверов, не по фиксированному inbound_id. Иначе клиенты из нестандартных inbound'ов не обновятся.

---

## Схема ответов

```python
class ServerResult(BaseModel):
    server: str
    ok: bool
    error: str | None = None

class RenewResponse(BaseModel):
    uuid: str
    email: str
    ok_count: int
    total: int
    results: list[ServerResult]

class ClientOut(BaseModel):
    uuid: str
    email: str
    expiry_ms: int        # Unix timestamp ms, 0 = бессрочно
    total_bytes: int      # лимит трафика в байтах, 0 = безлимит
    used_bytes: int
    days_left: int | None
    status: str           # "active" | "warning" | "expired"
    is_online: bool
    last_seen_ms: int | None
```

---

## Backend: пример GET /clients

```python
@app.get("/clients", response_model=list[ClientOut])
async def get_clients():
    servers = await get_all_servers()  # из БД бота
    # Параллельно по всем серверам:
    # 1. login()
    # 2. get_online_clients() → set email
    # 3. /panel/api/inbounds/list → iterate всех клиентов всех inbound'ов
    # 4. getClientTraffics/{email} → used_bytes
    # Дедупликация по UUID (берём первое вхождение)
    # Обновить last_seen для онлайн-клиентов
    # Подгрузить last_seen из SQLite
    # Сортировка: expired(0) → warning(1) → active(2), внутри по days_left
```

**Важно про 3x-ui API:**
- Авторизация через cookie (POST /login), не Bearer
- `settings` инбаунда — это JSON-строка, нужно `json.loads(inb["settings"])`
- Для создания клиента: POST `/panel/api/inbounds/addClient`, ID инбаунда — в теле запроса (`"id": inbound_id`), НЕ в URL
- SSL у панелей самоподписанный — отключить верификацию: `aiohttp.TCPConnector(ssl=False)`

---

## Frontend: ключевые компоненты

### SnapSlider (период/трафик)

```tsx
// Тик-шаги для периода
const PERIOD_STEPS = [
  { days: 7,   tick: '7 дн',  display: '7 дней'    },
  { days: 30,  tick: '1 мес', display: '1 месяц'   },
  { days: 90,  tick: '3 мес', display: '3 месяца'  },
  { days: 180, tick: '6 мес', display: '6 месяцев' },
  { days: 365, tick: '1 год', display: '1 год'     },
]
// Тик-шаги для трафика
const TRAFFIC_STEPS = [
  { gb: 0,    tick: '∞',    display: '∞ безлимит' },
  { gb: 1,    tick: '1',    display: '1 ГБ'       },
  { gb: 100,  tick: '100',  display: '100 ГБ'     },
  { gb: 300,  tick: '300',  display: '300 ГБ'     },
  { gb: 500,  tick: '500',  display: '500 ГБ'     },
  { gb: 1000, tick: '1000', display: '1000 ГБ'    },
]
```

Компонент `SnapSlider`:
- `<input type="range">` с кастомным CSS-thumb
- Вверху: отображаемое значение (красный текст, серая подложка-пилюля, анимация-вспышка при смене через `key={displayValue}`)
- Внизу: тик-метки кнопками — при выборе подсвечиваются зелёным (или цветом `accent`)
- Haptic feedback: `tg?.HapticFeedback?.selectionChanged()`

### CSS для слайдера

```css
.snap-slider {
  -webkit-appearance: none;
  width: 100%; height: 6px;
  border-radius: 3px; outline: none;
  cursor: pointer; touch-action: none;
}
.snap-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 56px; height: 28px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.5);
}
@keyframes snapFlash {
  0%   { background: rgba(255,255,255,0.35); }
  100% { background: rgba(255,255,255,0.12); }
}
.snap-value {
  display: inline-block;
  padding: 4px 16px; border-radius: 20px;
  background: rgba(255,255,255,0.12);
  color: #ff453a; font-size: 1.25rem; font-weight: 700;
  animation: snapFlash 0.4s ease-out;
}
```

### iOS glassmorphism (index.css)

```css
:root {
  --tg-bg:      var(--tg-theme-bg-color, #1c1c1e);
  --tg-bg2:     var(--tg-theme-secondary-bg-color, #2c2c2e);
  --tg-bg3:     rgba(255,255,255,0.08);
  --tg-text:    var(--tg-theme-text-color, #ffffff);
  --tg-hint:    var(--tg-theme-hint-color, #8e8e93);
  --tg-accent:  var(--tg-theme-button-color, #0a84ff);
  --tg-green:   #3fc26a;
  --tg-red:     #e84c4c;
  --safe-bottom: env(safe-area-inset-bottom, 0px);
}
.glass {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
}
.sheet {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--tg-bg2);
  border-radius: 20px 20px 0 0;
  padding-bottom: calc(16px + var(--safe-bottom));
  z-index: 50;
  overflow-x: hidden; /* важно — без этого сдвигается за экран */
  animation: slideUp 0.35s cubic-bezier(0.34, 1.2, 0.64, 1);
}
```

**Клавиатура на iOS:** НЕ использовать `visualViewport` listener для сдвига шита. Использовать `max-h-[90dvh]` (`dvh` = dynamic viewport height, автоматически учитывает клавиатуру). Добавить `overflow-y-auto` для скролла внутри шита. Поле ввода: `onFocus={e => e.currentTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest' })}`.

---

## Настройка бота (добавить кнопку Mini App)

```python
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

web_app_btn = KeyboardButton(
    text="📱 Mini App",
    web_app=WebAppInfo(url="https://ВАШ_ДОМЕН")
)
keyboard = ReplyKeyboardMarkup(keyboard=[[web_app_btn, ...]], resize_keyboard=True)
```

---

## Docker Compose (miniapp)

```yaml
services:
  miniapp-api:
    build:
      context: ..
      dockerfile: miniapp/backend/Dockerfile
    volumes:
      - ../data:/app/api/data
    ports:
      - "8001:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s; timeout: 10s; retries: 3

  miniapp-web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: /api
    ports:
      - "8088:80"
    depends_on:
      miniapp-api:
        condition: service_healthy
```

Backend Dockerfile — монтирует `/app/bot` из основного бота, чтобы импортировать `database.py` и `xui_client.py`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app/api
COPY miniapp/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY miniapp/backend/main.py .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

В `main.py`: `sys.path.insert(0, "/app/bot")` — чтобы импортировать из бота.

---

## Nginx (nginx.conf для miniapp-web)

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  location /api/ {
    proxy_pass http://miniapp-api:8000/;
    proxy_set_header Host $host;
  }

  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

SSL-терминация — на внешнем реверс-прокси (certbot + nginx на хосте).

---

## Last-seen tracking (SQLite)

```python
# Инициализация при старте
CREATE TABLE IF NOT EXISTS client_last_seen (
    email TEXT PRIMARY KEY,
    last_seen INTEGER NOT NULL  -- Unix timestamp ms
)

# При каждом GET /clients: обновлять last_seen для онлайн-клиентов
# При рендере: "сегодня" / "вчера" / "N дн. назад" / "N нед. назад"
```

---

## Что адаптировать под конкретный бот

1. **`get_all_servers()`** — функция из БД бота, возвращает список серверов с полями `key`, `url`, `username`, `password`, `inbound_id`
2. **`get_setting(key)`** — получить настройку (например `default_username`, `default_password`)
3. **`XUIClient`** — HTTP-клиент к 3x-ui. Нужны методы: `login()`, `logout()`, `get_inbounds_list()`, `get_online_clients()`, `create_client(...)`, `update_client_params(...)`, `delete_client(...)`
4. **Группы серверов** — например "bundle" (несколько серверов с одним UUID) или одиночный. Адаптировать логику создания под свои серверы
5. **URL подписки** — если есть subscription-сервер, подставить свой URL
6. **URL happ-redirect** — редирект-сервер для добавления в Happ: `http://ВАШ_СЕРВЕР:8090/r/happ/{uuid}?name=ИМЯ`; если нет — убрать эту часть из сообщения клиенту
7. **ADMIN_ID** — ID администратора в Telegram (для send_card если нужно)

---

## Известные подводные камни

| Проблема | Решение |
|----------|---------|
| SSL у 3x-ui панелей самоподписанный | `aiohttp.TCPConnector(ssl=False)` |
| addClient возвращает ошибку | endpoint `/panel/api/inbounds/addClient` (БЕЗ ID в URL!) — ID инбаунда идёт в теле |
| Keyboard на iOS сдвигает шит | Убрать visualViewport listener, использовать `max-h-[90dvh]` |
| Sheet выезжает за ширину экрана | `overflow-x: hidden` на `.sheet` |
| Клиент не находится при продлении | Искать UUID во ВСЕХ inbound'ах всех серверов |
| xui панель возвращает HTML вместо JSON | Оборачивать parse в try/except, пропускать такой сервер |
| `settings` инбаунда — строка, не dict | Всегда `json.loads(inb.get("settings", "{}"))` |

---

## Порядок реализации

1. Поднять FastAPI с `/health` и `GET /clients` (читать из одного тестового сервера)
2. Настроить Docker Compose, убедиться что frontend видит API через `/api/`
3. Реализовать `ClientList.tsx` — список карточек
4. Добавить `ClientSheet.tsx` — детали + продление
5. Добавить `CreateSheet.tsx` — форма создания
6. Реализовать `POST /clients`, `POST /clients/{uuid}/renew`, `DELETE /clients/{uuid}`
7. Добавить last_seen tracking в SQLite
8. Настроить SSL через certbot на домене
9. Добавить кнопку Mini App в Telegram-бота
