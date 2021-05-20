import os

import pytest

from tasks.models import Doc
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
    data = {}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/doc/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_doc_create_and_delete_with_right_file_type(user_client,
                                                            create_task):
    doc_file = create_text_file('testfile')
    task = create_task
    data = {'doc_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/doc/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/files/{task["id"]}/testfile.pdf'
    assert os.path.isfile(filepath) is True
    doc_id = Doc.objects.all()[0].id
    response2 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/doc/{doc_id}/')
    assert response2.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_04_task_doc_update_change_uploaded_file(user_client,
                                                 create_task):
    doc_file = create_text_file('testfile')
    task = create_task
    data = {'doc_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/doc/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/files/{task["id"]}/testfile.pdf'
    assert os.path.isfile(filepath) is True
    doc_file2 = create_text_file('testfile2')
    data2 = {'doc_file': doc_file2}
    doc_id = Doc.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{task["id"]}/doc/{doc_id}/', data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/files/{task["id"]}/testfile2.pdf'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/doc/{doc_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_05_task_doc_create_with_wrong_file_type(user_client, create_task):
    image = create_image_file('small')
    task = create_task
    data = {'doc_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/doc/', data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_06_get_comment_docs_list(user_client, create_comment):
    task, comment = create_comment
    response = user_client.get(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/')
    assert response.status_code != 404, \
        (
            'Страница `/v1/tasks/task/{task_id}/comment/{comment_id/doc}` не найдена, '
            'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_07_get_comment_single_doc(user_client, create_comment):
    task, comment = create_comment
    doc = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data={}).json()
    response = user_client.get(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/{doc["id"]}/')
    assert response.status_code != 404, \
        (
            'Страница `/v1/tasks/task/{task_id}/comment/{comment_id/doc}` не найдена, '
            'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_08_comment_doc_create_without_file(user_client, create_comment):
    task, comment = create_comment
    data = {}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_09_comment_doc_create_and_delete_with_right_file_type(user_client,
                                                               create_comment):
    doc_file = create_text_file('testfile')
    task, comment = create_comment
    data = {'doc_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/files/{task["id"]}/testfile.pdf'
    assert os.path.isfile(filepath) is True
    doc_id = Doc.objects.all()[0].id
    response2 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/{doc_id}/')
    assert response2.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_10_comment_doc_update_change_uploaded_file(user_client,
                                                    create_comment):
    doc_file = create_text_file('testfile')
    task, comment = create_comment
    data = {'doc_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/files/{task["id"]}/testfile.pdf'
    assert os.path.isfile(filepath) is True
    doc_file2 = create_text_file('testfile2')
    data2 = {'doc_file': doc_file2}
    doc_id = Doc.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/{doc_id}/',
        data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/files/{task["id"]}/testfile2.pdf'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/{doc_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_11_comment_doc_create_with_wrong_file_type(user_client,
                                                    create_comment):
    image = create_image_file('small')
    task, comment = create_comment
    data = {'doc_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'
