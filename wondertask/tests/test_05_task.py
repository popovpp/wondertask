import pytest

from django.contrib.auth import get_user_model

from tasks.models import Task

User = get_user_model()


@pytest.mark.django_db()
def test_01_task_create(user_client):
    data = {
        "title": "test_task",
        "creator": 1,
    }
    response = user_client.post(f'/v1/tasks/task/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_02_get_task_list(user_client, create_task):
    create_task
    response = user_client.get(f'/v1/tasks/task/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_03_get_single_task(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_04_patch_task(user_client, create_task):
    task = create_task
    data = {'title': '1234'}
    response = user_client.patch(f'/v1/tasks/task/{task["id"]}/',
                                 data=data)
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_05_delete_comment(user_client, create_task):
    task = create_task
    response = user_client.delete(f'/v1/tasks/task/{task["id"]}/')
    assert response.status_code == 204, f'{response.json()}'


@pytest.mark.django_db()
def test_06_get_task_tree_list(user_client, create_task):
    create_task
    data = {
        "title": "test_task",
        "creator": 1,
        "parent": 1
    }
    user_client.post(f'/v1/tasks/task/', data=data)
    response = user_client.get(f'/v1/tasks/tasktree/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_07_get_task_tree_children(user_client, create_task):
    task1 = create_task
    data = {
        "title": "test_task2",
        "creator": 1,
        "parent": 1
    }
    user_client.post(f'/v1/tasks/task/', data=data)
    response = user_client.get(f'/v1/tasks/tasktree/{task1["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_08_get_my_task_list(user_client, create_task):
    response = user_client.get(f'/v1/tasks/task/my/')
    assert response.status_code == 200
    assert response.json()['results'] == [create_task]
