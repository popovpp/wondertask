import pytest
from django.contrib.auth import get_user_model

from tasks.models import Task

User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_01_task_schedule_create(user_client, celery_worker, create_user):
    task = Task.objects.create(title="title", creator=create_user)
    data = {
        "task": task.id,
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
    assert response.status_code == 201


@pytest.mark.django_db()
def test_02_get_task_schedule_list(user_client, create_schedule_task):
    response = user_client.get(f'/v1/tasks/repeats/')
    assert response.status_code == 200
    assert response.json()['count'] > 0


@pytest.mark.django_db()
def test_03_get_single_task_schedule(user_client, create_schedule_task):
    response = user_client.get(f'/v1/tasks/repeats/{create_schedule_task["id"]}/')
    assert response.status_code == 200
    assert response.json()['task'] == create_schedule_task['task']


@pytest.mark.django_db()
def test_04_task_schedule_update(user_client, create_schedule_task):
    data = {
        "task": create_schedule_task['task'],
        "crontab": {
            "minute": "0",
            "hour": "0",
            "day_of_week": "*/1",
            "day_of_month": "*",
            "month_of_year": "*",
            "timezone": "Europe/Moscow"
        }
    }
    response = user_client.put(f'/v1/tasks/repeats/{create_schedule_task["id"]}/',
                               data=data, format='json')
    assert response.status_code == 200
    assert response.json()['crontab'] == data['crontab']


@pytest.mark.django_db()
def test_05_task_schedule_patch(user_client, create_schedule_task):
    data = {
        "task": create_schedule_task['task'],
        "crontab": {
            "minute": "10",
        }
    }
    response = user_client.patch(f'/v1/tasks/repeats/{create_schedule_task["id"]}/',
                                 data=data, format='json')
    assert response.status_code == 200
    assert response.json()['crontab']["minute"] == data['crontab']["minute"]


@pytest.mark.django_db()
def test_06_task_schedule_delete(user_client, create_schedule_task):
    response = user_client.delete(f'/v1/tasks/repeats/{create_schedule_task["id"]}/')
    assert response.status_code == 204
