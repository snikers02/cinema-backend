import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Ініціалізуємо HTTP додаток Django
django_asgi_app = get_asgi_application()

# Імпортуємо роутинг кімнат (ми створимо цей файл наступним кроком)
import apps.rooms.routing 

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.rooms.routing.websocket_urlpatterns
        )
    ),
})