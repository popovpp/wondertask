import pytest

from tests.common import create_text_file, create_image_file


@pytest.mark.django_db()
def test_01_get_task_doc_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/doc/')
    assert response.status_code != 404, \
        ('Страница `/v1/tasks/task/{task_id}/doc/` не найдена, '
         'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_02_task_doc_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_doc_create_with_right_file_type(user_client, create_task):
    doc_file = create_text_file()
    task = create_task
    data = {'text': 'asdf',
            'doc_file': doc_file}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_doc_create_with_wrong_file_type(user_client, create_task):
    image = create_image_file()
    task = create_task
    data = {'text': 'asdf',
            'doc_file': image}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 400, f'{response.json()}'
