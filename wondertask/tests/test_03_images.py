import os

import pytest

from tasks.models import Image
from tests.common import create_image_file, create_audio_file, create_text_file


@pytest.mark.django_db()
def test_01_get_task_image_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/image/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_02_task_image_create_without_file(user_client, create_task):
    task = create_task
    data = {}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/', data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_image_create_with_right_file_type(user_client, create_task):
    image = create_image_file('small')
    task = create_task
    data = {'image_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/image/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    image_id = Image.objects.all()[0].id
    user_client.delete(f'/v1/tasks/task/{task["id"]}/image/{image_id}/')


@pytest.mark.django_db()
def test_04_task_image_delete(user_client, create_task):
    image = create_image_file('small')
    task = create_task
    data = {'image_file': image}
    user_client.post(f'/v1/tasks/task/{task["id"]}/image/', data=data)
    image_id = Image.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/image/{image_id}/')
    assert response.status_code == 204, f'{response.json()}'


@pytest.mark.django_db()
def test_05_task_image_update_change_uploaded_file(user_client, create_task):
    image = create_image_file('small')
    task = create_task
    data = {'image_file': image}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/images/{task["id"]}/small.gif'
    assert os.path.isfile(filepath) is True
    image2 = create_image_file('small2')
    data2 = {'image_file': image2}
    image_id = Image.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{task["id"]}/image/{image_id}/', data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/images/{task["id"]}/small2.gif'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/image/{image_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_06_task_image_create_with_wrong_file_type(user_client, create_task):
    audio = create_audio_file('music')
    task = create_task
    data = {'image_file': audio}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/', data=data, format='json')
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_07_get_comment_image_list(user_client, create_comment):
    response = user_client.get(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_08_get_comment_single_image(user_client, create_comment):
    image = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data={}).json()
    response = user_client.get(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/{image["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_09_comment_image_create_without_file(user_client, create_comment):
    data = {}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_10_comment_image_create_with_right_file_type(user_client, create_comment):
    image = create_image_file('small')
    data = {'image_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'
    image_id = Image.objects.all()[0].id
    user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/{image_id}/')


@pytest.mark.django_db()
def test_11_comment_image_delete(user_client, create_comment):
    image = create_image_file('small')
    data = {'image_file': image}
    user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data=data)
    image_id = Image.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/{image_id}/')
    assert response.status_code == 204, f'{response.json()}'


@pytest.mark.django_db()
def test_12_task_image_update_change_uploaded_file(user_client, create_comment):
    image = create_image_file('small')
    data = {'image_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/images/{create_comment["task"]}/small.gif'
    assert os.path.isfile(filepath) is True
    image2 = create_image_file('small2')
    data2 = {'image_file': image2}
    image_id = Image.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/{image_id}/',
        data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/images/{create_comment["task"]}/small2.gif'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/{image_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_13_comment_image_create_with_wrong_file_type(user_client, create_comment):
    doc_file = create_text_file('testfile')
    data = {'image_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/image/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'
