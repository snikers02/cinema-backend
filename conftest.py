import pytest


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
