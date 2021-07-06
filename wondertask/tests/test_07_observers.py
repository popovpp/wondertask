import pytest

from tasks.models import Observer


@pytest.mark.django_db()
def test_01_get_task_observers_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/observers/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_02_get_task_single_observer(user_client, create_task, create_user):
    task = create_task
    data = {"observer": create_user.id}
    user_client.post(f'/v1/tasks/task/{task["id"]}/observers/', data=data)
    observer_id = Observer.objects.all()[0].id
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/observers/{observer_id}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_observers_create(user_client, create_task, create_user):
    task = create_task
    data = {"observer": create_user.id}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/observers/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_observers_delete_file_with_object(user_client, create_task, create_user):
    task = create_task
    data = {"observer": create_user.id}
    user_client.post(f'/v1/tasks/task/{task["id"]}/observers/', data=data)
    observer_id = Observer.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/observers/{observer_id}/')
    assert response.status_code == 204, f'{response.json()}'
