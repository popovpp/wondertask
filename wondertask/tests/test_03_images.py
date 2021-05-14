import pytest

from tests.common import create_image_file, create_audio_file, create_text_file


@pytest.mark.django_db()
def test_01_get_task_image_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/image/')
    assert response.status_code != 404, \
        ('Страница `/v1/tasks/task/{task_id}/image/` не найдена, '
         'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_02_task_image_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_image_create_with_right_file_type(user_client, create_task):
    image = create_image_file()
    task = create_task
    data = {'text': 'asdf',
            'image_file': image}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_image_create_with_wrong_file_type(user_client, create_task):
    audio = create_audio_file()
    task = create_task
    data = {'text': 'asdf',
            'image_file': audio}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data, format='json')
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_05_get_comment_image_list(user_client, create_comment):
    task, comment = create_comment
    response = user_client.get(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/')
    assert response.status_code != 404, \
        (
            'Страница `/v1/tasks/task/{task_id}/comment/{comment_id/image}` не найдена, '
            'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_06_comment_image_create_without_file(user_client, create_comment):
    task, comment = create_comment
    data = {'text': 'asdf'}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_07_comment_image_create_with_file(user_client, create_comment):
    image = create_image_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'image_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_08_comment_image_create_with_wrong_file_type(user_client,
                                                      create_comment):
    doc_file = create_text_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'image_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'
