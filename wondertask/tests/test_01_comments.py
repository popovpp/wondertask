import pytest

from django.contrib.auth import get_user_model

from tasks.models import Comment

User = get_user_model()


@pytest.mark.django_db()
def test_01_comment_create(user_client, create_task, create_user):
    data = {'author': create_user.id, 'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/comment/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_02_get_comment_list(user_client, create_comment):
    response = user_client.get(f'/v1/tasks/task/{create_comment["task"]}/comment/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_03_get_single_comment(user_client, create_comment):
    response = user_client.get(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_04_patch_comment(user_client, create_comment):
    new_text = "some new comment text"
    response = user_client.patch(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/',
        data={'text': new_text})
    assert response.status_code == 200, f'{response.json()}'
    assert response.json()['text'] == new_text


@pytest.mark.django_db()
def test_05_delete_comment(user_client, create_comment):
    current_comment_count = Comment.objects.all().count()
    response = user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/')
    assert response.status_code == 204, f'{response.json()}'
    assert Comment.objects.all().count() == current_comment_count - 1
