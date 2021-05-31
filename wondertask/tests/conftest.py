import pytest

from accounts.models import User


@pytest.fixture
def user_client():
    from rest_framework.test import APIClient
    user = User.objects.create(email='user@gmail.com', password='1234567')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def create_task(user_client):
    task_data1 = {
        'title': 'test_title1',
        'creator': 1,
    }
    response = user_client.post('/v1/tasks/task/', data=task_data1).json()
    return response


@pytest.fixture
def create_comment(user_client, create_task):
    task = create_task
    data = {'author': 1,
            'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/comment/',
                                data=data).json()
    return task, response


@pytest.fixture
def create_tag(user_client):
    data = {'name': 'project'}
    response = user_client.post(f'/v1/tasks/tags/', data=data).json()
    return response
