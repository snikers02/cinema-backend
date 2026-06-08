# Architecture — Cinema Backend (Microkernel)

## Огляд

Проєкт реалізує **спільний перегляд відео в реальному часі** (кімнати, чат, синхронізація відтворення, реакції, соціальні функції, досягнення).

Архітектурний стиль: **Microkernel** — ізольоване ядро + підключаємі плагіни, зв'язані через подієву шину (Django Signals).

## Шари та відповідальності

| Шар | Шлях | Відповідальність |
|-----|------|------------------|
| Kernel | `apps/users/`, `apps/rooms/` | Користувачі, JWT, кімнати, invite-коди, WebSocket transport |
| Core | `core/` | Settings, URL routing, ASGI, middleware |
| Plugins | `plugins/*/` | Бізнес-фічі: movies, sync, chat, reactions, social, activity, achievements |
| Shared tests | `tests/` | Фікстури, хелпери для всіх модулів |

## Event Bus (Observer Pattern)

Сигнали визначені в ядрі (`apps/rooms/signals.py`):

- `room_created_signal` — нова кімната створена; плагіни підписуються для ініціалізації стану.
- `socket_message_signal` — вхідне WS-повідомлення; плагіни фільтрують за `message_type`.

```python
# plugins/<plugin>/signals.py
from django.dispatch import receiver
from apps.rooms.signals import socket_message_signal

@receiver(socket_message_signal)
def handle_event(sender, room_id, user, message_type, data, **kwargs):
    if message_type == 'my.event':
        ...
```

**Правило:** плагін імпортує сигнали з `apps`, але `apps` ніколи не імпортує `plugins`.

## Strategy Pattern

Варіативна логіка виноситься в окремі стратегії/функції:

- `plugins/sync/` — правила хто може керувати відтворенням (`check_user_can_control_playback`, `RoomPlaybackRules`, `RoomAuthorizedController`).
- `plugins/movies/` — різні джерела медіа (локальний файл vs YouTube URL).

При додаванні нової стратегії: Protocol/ABC + окрема імплементація + unit-тести для кожної гілки.

## SOLID у практиці

### Single Responsibility
- `RoomConsumer` — лише WS connect/disconnect/broadcast.
- Serializer — валідація та серіалізація.
- Signal handler — одна реакція на одну подію.

### Open/Closed
Нова фіча = новий плагін + реєстрація в `INSTALLED_APPS`, без зміни `apps/rooms/consumers.py`.

### Dependency Inversion
```python
from typing import Protocol

class PlaybackRuleStrategy(Protocol):
    def can_control(self, user, room_id) -> bool: ...
```

Сервіс приймає `PlaybackRuleStrategy`, тести підставляють mock/stub.

## Структура плагіна

```
plugins/my_plugin/
├── __init__.py
├── apps.py          # MyPluginConfig
├── models.py
├── serializers.py
├── views.py         # REST API (якщо потрібно)
├── signals.py       # @receiver handlers
├── urls.py
└── tests.py         # unit + integration
```

## WebSocket Flow

```
Client → RoomConsumer.receive() → socket_message_signal.send()
       → Plugin handlers → DB / broadcast → group_send()
```

## База даних

| Середовище | Engine |
|------------|--------|
| Production / Docker | PostgreSQL (`DATABASE_URL`) |
| CI / локальні тести | SQLite in-memory (`conftest.py`) |

Redis — channel layers для WebSocket groups (не для персистентних даних).

## Діаграми

UML/ERD: `docs/database-uml.puml`, `docs/database-erd.md`.

## Анти-патерни (уникати)

- Імпорт `plugins.*` з `apps/` або `core/`
- Бізнес-логіка всередині `RoomConsumer`
- Прямі залежності між плагінами (тільки через сигнали або спільні kernel-моделі)
- God classes з 500+ рядків без розбиття
