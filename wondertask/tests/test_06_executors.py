import pytest

from tasks.models import Executor


@pytest.mark.django_db()
def test_01_get_task_executors_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/executors/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_02_get_task_single_executor(user_client, create_task, create_user):
    task = create_task
    data = {"executor": create_user.id}
    user_client.post(f'/v1/tasks/task/{task["id"]}/executors/', data=data)
    executor_id = Executor.objects.all()[0].id
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/executors/{executor_id}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_executors_create(user_client, create_task, create_user):
    task = create_task
    data = {"executor": create_user.id}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/executors/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_executors_delete_file_with_object(user_client, create_task, create_user):
    task = create_task
    data = {"executor": create_user.id}
    user_client.post(f'/v1/tasks/task/{task["id"]}/executors/', data=data)
    executor_id = Executor.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/executors/{executor_id}/')
    assert response.status_code == 204, f'{response.json()}'
