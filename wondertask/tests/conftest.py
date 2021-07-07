import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture(scope='session')
def celery_config():
    import settings
    return {
        'broker_url': settings.CELERY_BROKER_URL,
        'result_backend': settings.CELERY_RESULT_BACKEND,
    }


@pytest.fixture(scope="session")
def create_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        user = User.objects.create(email="user@exapmple.com", password="1235", full_name="name")
    return user


@pytest.fixture(scope="session")
def user_client(create_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=create_user)
    return client


@pytest.fixture(scope="session")
def create_task(django_db_blocker, user_client):
    with django_db_blocker.unblock():
        data = {
            'title': 'test_title1',
        }
        response = user_client.post('/v1/tasks/task/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_comment(django_db_blocker, user_client, create_task):
    with django_db_blocker.unblock():
        task = create_task
        data = {'author': 1,
                'text': 'asdf'}
        response = user_client.post(f'/v1/tasks/task/{task["id"]}/comment/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_tag(django_db_blocker, user_client):
    with django_db_blocker.unblock():
        data = {'name': 'project'}
        response = user_client.post(f'/v1/tasks/tags/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_group(django_db_blocker, user_client):
    with django_db_blocker.unblock():
        data = {'group_name': 'some group'}
        response = user_client.post(f'/v1/tasks/groups/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_system_tag(django_db_blocker, user_client):
    with django_db_blocker.unblock():
        data = {'name': '$шаблонная'}
        response = user_client.post(f'/v1/tasks/systemtags/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_task_with_parent(django_db_blocker, user_client, create_task):
    with django_db_blocker.unblock():
        data = {
            'title': 'test_title1',
            'parent': create_task['id']
        }
        response = user_client.post('/v1/tasks/task/', data=data).json()
    return response


@pytest.fixture(scope="session")
def create_task_with_tags(django_db_blocker, user_client, create_task):
    with django_db_blocker.unblock():
        data = {"tags": ["проект"]}
        response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/add-tags/', data=data)
    return response.json()


@pytest.fixture(scope="session")
def create_task_with_system_tags(django_db_blocker, user_client, create_task, create_system_tag):
    with django_db_blocker.unblock():
        data = {"tags": [create_system_tag["name"]]}
        response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/add-tags/', data)
    return response.json()


@pytest.fixture(scope="session")
def create_schedule_task(django_db_blocker, user_client, create_task):
    with django_db_blocker.unblock():
        data = {
            "task": create_task["id"],
            "number_of_times": 5,
            "crontab": {
                "minute": "0",
                "hour": "0",
                "day_of_week": "*",
                "day_of_month": "*/1",
                "month_of_year": "*",
                "timezone": "Europe/Moscow"
            }
        }
        response = user_client.post(f'/v1/tasks/repeats/', data=data, format='json')
    return response.json()


@pytest.fixture(scope="module")
def create_notification(django_db_blocker, user_client, create_user):
    with django_db_blocker.unblock():
        data = {
            "message": "Some message",
            "type": "ACTION",
            "recipients": [create_user.id]
        }
        response = user_client.post(f'/v1/journals/notifications/', data=data)
    return response.json()
