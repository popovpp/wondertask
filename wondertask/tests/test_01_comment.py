import pytest

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db()
def test_01_comment_create(user_client, create_comment):
    task, comment = create_comment
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/comment/',
                                data=data)
    assert response.status_code == 201, \
        ('Страница `/v1/tasks/task/{task_id}/comment/` не найдена, '
         'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_02_get_comment_list(user_client, create_comment):
    task, comment = create_comment
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/comment/')
    assert response.status_code != 404, \
        ('Страница `/v1/tasks/task/{task_id}/comment/` не найдена, '
         'проверьте этот адрес в *urls.py*')
