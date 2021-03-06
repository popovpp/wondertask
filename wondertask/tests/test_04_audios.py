import os

import pytest

from tasks.models import Audio
from tests.common import create_audio_file, create_text_file


@pytest.mark.django_db()
def test_01_get_task_audio_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/audio/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_02_task_audio_create_without_file(user_client, create_task):
    task = create_task
    data = {}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/', data=data, format='json')
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_audio_create_with_right_file_type(user_client, create_task):
    audio = create_audio_file('music')
    task = create_task
    data = {'audio_file': audio}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/audio/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    audio_id = Audio.objects.all()[0].id
    user_client.delete(f'/v1/tasks/task/{task["id"]}/audio/{audio_id}/')


@pytest.mark.django_db()
def test_03_task_audio_delete(user_client, create_task):
    audio = create_audio_file('music')
    task = create_task
    data = {'audio_file': audio}
    user_client.post(
        f'/v1/tasks/task/{task["id"]}/audio/', data=data)
    audio_id = Audio.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/audio/{audio_id}/')
    assert response.status_code == 204, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_audio_update_change_uploaded_file(user_client, create_task):
    audio = create_audio_file('music')
    task = create_task
    data = {'audio_file': audio}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/audio/', data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/audio/{task["id"]}/music.mp3'
    assert os.path.isfile(filepath) is True
    audio2 = create_audio_file('music2')
    data2 = {'audio_file': audio2}
    audio_id = Audio.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{task["id"]}/audio/{audio_id}/', data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/audio/{task["id"]}/music2.mp3'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/audio/{audio_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_05_task_audio_create_with_wrong_file_type(user_client, create_task):
    doc_file = create_text_file('testfile')
    task = create_task
    data = {'audio_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/audio/', data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_06_get_comment_audio_list(user_client, create_comment):
    response = user_client.get(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_07_get_comment_single_audio(user_client, create_comment):
    audio = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data={}).json()
    response = user_client.get(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/{audio["id"]}/')
    assert response.status_code == 200, f'{response.json()}'


@pytest.mark.django_db()
def test_08_comment_audio_create_without_file(user_client, create_comment):
    data = {}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_09_comment_audio_create_with_right_file_type(user_client, create_comment):
    audio_file = create_audio_file('music')
    data = {'audio_file': audio_file}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'
    audio_id = Audio.objects.all()[0].id
    user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/{audio_id}/')


@pytest.mark.django_db()
def test_09_comment_audio_delete(user_client, create_comment):
    audio_file = create_audio_file('music')
    data = {'audio_file': audio_file}
    user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data=data)
    audio_id = Audio.objects.all()[0].id
    response = user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/{audio_id}/')
    assert response.status_code == 204, f'{response.json()}'


@pytest.mark.django_db()
def test_10_comment_audio_update_change_uploaded_file(user_client, create_comment):
    audio = create_audio_file('music')
    data = {'audio_file': audio}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/audio/{create_comment["task"]}/music.mp3'
    assert os.path.isfile(filepath) is True
    audio2 = create_audio_file('music2')
    data2 = {'audio_file': audio2}
    audio_id = Audio.objects.all()[0].id
    response2 = user_client.patch(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/{audio_id}/',
        data=data2)
    assert response2.status_code == 200, f'{response.json()}'
    filepath2 = f'media/audio/{create_comment["task"]}/music2.mp3'
    assert os.path.isfile(filepath2) is True
    response3 = user_client.delete(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/{audio_id}/')
    assert response3.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_11_comment_audio_create_with_wrong_file_type(user_client, create_comment):
    doc_file = create_text_file('testfile')
    data = {'audio_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{create_comment["task"]}/comment/{create_comment["id"]}/audio/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'
