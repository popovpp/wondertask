import os

import pytest

from tasks.models import Audio
from tests.common import create_audio_file, create_text_file


@pytest.mark.django_db()
def test_01_get_task_audio_list(user_client, create_task):
    task = create_task
    response = user_client.get(f'/v1/tasks/task/{task["id"]}/audio/')
    assert response.status_code != 404, \
        ('Страница `/v1/tasks/task/{task_id}/audio/` не найдена, '
         'проверьте этот адрес в *urls.py*')


@pytest.mark.django_db()
def test_02_task_audio_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data, format='json')
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_03_task_audio_create_and_delete_with_right_file_type(user_client,
                                                              create_task):
    audio = create_audio_file()
    task = create_task
    data = {'text': 'asdf',
            'audio_file': audio}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'
    filepath = f'media/audio/{task["id"]}/music.mp3'
    assert os.path.isfile(filepath) is True
    audio_id = Audio.objects.all()[0].id
    response2 = user_client.delete(
        f'/v1/tasks/task/{task["id"]}/audio/{audio_id}/',
        data=data)
    assert response2.status_code == 204, f'{response.json()}'
    assert os.path.isfile(filepath) is False


@pytest.mark.django_db()
def test_04_task_audio_create_with_wrong_file_type(user_client, create_task):
    doc_file = create_text_file('testfile')
    task = create_task
    data = {'text': 'asdf',
            'audio_file': doc_file}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data)
    assert response.status_code == 400, f'{response.json()}'
