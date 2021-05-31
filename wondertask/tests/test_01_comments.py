import pytest

from django.contrib.auth import get_user_model

from tasks.models import Comment

User = get_user_model()


@pytest.mark.django_db()
def test_01_comment_create(user_client, create_comment):
    task, comment = create_comment
    data = {'author': 1,
            'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/comment/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_02_get_comment_list(user_client, create_comment):
    task, comment = create_comment
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/comment/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_03_get_single_comment(user_client, create_comment):
    task, comment = create_comment
    response = user_client.get(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_04_patch_comment(user_client, create_comment):
    task, comment = create_comment
    data = {'text': '1234'}
    response = user_client.patch(f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/',
                                 data=data)

    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_05_delete_comment(user_client, create_comment):
    task, comment = create_comment
    assert Comment.objects.all().count() == 1
    response = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/')
    assert response.status_code == 204, f'{response.json()}'
