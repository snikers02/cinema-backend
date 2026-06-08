# Testing Strategy — Cinema Backend

## Цілі Quality Gate

| Метрика | Мінімум |
|---------|---------|
| Code Coverage | **≥ 70%** |
| Кількість тестів | **~200+** |
| Bugs / Vulnerabilities (Sonar) | **0** |
| Code Smells | **A або B** |

## Стек

- **pytest** + **pytest-django** + **pytest-cov**
- **unittest.mock** — ізоляція шарів (signals, WebSocket, зовнішні сервіси)
- **Django TestCase** / **APIClient** — інтеграційні тести REST API
- **SQLite in-memory** — швидкі тести без PostgreSQL (`conftest.py`)

## Запуск

```bash
# Локально
pip install pytest pytest-django pytest-cov
pytest --cov=. --cov-report=xml --cov-report=html

# У Docker
docker-compose exec web pytest --cov=. --cov-report=xml --cov-report=html
```

## Звіти (CI Artifacts)

Після кожного запуску pytest генерує:

| Файл | Призначення |
|------|-------------|
| `coverage.xml` | Інтеграція з SonarCloud (`sonar.python.coverage.reportPaths`) |
| `htmlcov/` | HTML-звіт для візуального перегляду непокритих рядків |

Опційно для Sonar/JUnit:

```bash
pytest --cov=. --cov-report=xml --cov-report=html --junitxml=junit.xml
```

Артефакти завантажуються в CI (`.github/workflows/ci.yml` → `actions/upload-artifact`).

## TDD Workflow для ШІ-агентів

1. **Прочитай** існуючі тести в модулі (`apps/*/tests.py`, `plugins/*/tests.py`).
2. **Напиши тест** що падає (red) — edge cases, негативні сценарії, permissions.
3. **Реалізуй** мінімальний код (green).
4. **Рефактор** без зміни поведінки.
5. **Перевір покриття** — ціль ≥ 70% на змінених файлах.

## Структура тестів

```
apps/users/test_auth.py          # JWT login/register
apps/users/test_serializers.py   # валідація
apps/rooms/tests.py              # CRUD кімнат
apps/rooms/test_consumers.py     # WebSocket
plugins/sync/tests.py            # playback rules (Strategy)
plugins/movies/test_signals.py   # Observer (signals)
plugins/chat/tests.py            # chat API
tests/helpers.py                 # create_test_user(), response_list()
conftest.py                      # SQLite in-memory DB
```

## Патерни тестування

### Хелпер для користувачів
```python
from tests.helpers import create_test_user

user = create_test_user(username='tester')
```

### Тестування Signal handlers (Observer)
```python
import plugins.signals  # noqa: F401 — register handler
from apps.rooms.signals import socket_message_signal

socket_message_signal.send(
    sender=None,
    room_id=room_id,
    user=user,
    message_type='chat.message',
    data={'text': 'Hello'},
)
```

### Mock для ізоляції
```python
from unittest.mock import patch

@patch('apps.rooms.consumers.get_channel_layer')
def test_broadcast(mock_layer):
    ...
```

### REST API
```python
from rest_framework.test import APIClient

client = APIClient()
client.force_authenticate(user=user)
response = client.post('/api/users/login/', {'username': 'x', 'password': 'y'})
```

## Edge Cases (обов'язково покривати)

- Неавторизований / AnonymousUser
- Неіснуючий `room_id` (uuid)
- Порожні рядки, невалідний JSON, невідомий `message_type`
- Дублікати, race conditions (`IntegrityError` + retry)
- Права доступу: creator vs member vs unauthorized controller

## Генерація тестових даних

- Унікальні username/email через `create_test_user` (лічильник у `helpers.py`)
- `uuid.uuid4()` для room_id у signal-тестах
- Factory-патерн дозволений для складних об'єктів

## CI Pipeline (GitHub Actions)

Файл: `.github/workflows/ci.yml`

1. **Build** — `pip install -r requirements.lock`
2. **Lint** — `flake8`
3. **Test & Coverage** — `pytest --cov=. --cov-report=xml --cov-report=html`
4. **SonarCloud Scan** — Quality Gate
5. **Artifacts** — upload `coverage.xml` + `htmlcov/`

## SonarCloud

- Конфіг: `sonar-project.properties`
- Виключення: `**/migrations/**`, `**/tests/**`, `venv/**`
- Покриття: `coverage.xml` після pytest

## Що НЕ тестувати

- Django auto-generated migrations
- Сторонні бібліотеки (Django, DRF, Channels)
- Тривіальні getter/setter без логіки

## Перед здачею PR

- [ ] `pytest` — усі тести green
- [ ] Coverage ≥ 70%
- [ ] `flake8` без критичних помилок
- [ ] SonarCloud Quality Gate passed
- [ ] Артефакти доступні для завантаження в GitHub Actions
