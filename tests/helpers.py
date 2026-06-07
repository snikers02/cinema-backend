from django.contrib.auth import get_user_model

User = get_user_model()
_counter = 0


def create_test_user(username='user', password='password123', **kwargs):
    global _counter
    _counter += 1
    kwargs.setdefault('email', f'{username}_{_counter}@test.com')
    return User.objects.create_user(username=username, password=password, **kwargs)


def response_list(data):
    return data.get('results', data) if isinstance(data, dict) else data
