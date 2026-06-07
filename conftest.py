import os
import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-ci-runs')


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
