import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


@pytest.fixture
def user_client():
    from rest_framework.test import APIClient
    user = User.objects.create(email='user@gmail.com', password='1234567')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def create_task(user_client):
    task_data1 = {
        'title': 'test_title1',
        'creator': 1
    }
    response = user_client.post('/v1/tasks/task/', data=task_data1).json()
    return response


@pytest.fixture
def create_comment(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/comment/',
                                data=data).json()
    return task, response


def create_text_file():
    test_file = "testfile.txt"
    with open(test_file, "w") as f:
        f.write("Hello World")
    f = open(test_file, 'r')
    return f


def create_image_file():
    SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B'
                 )
    UPLOADED = SimpleUploadedFile(
        name='small.gif',
        content=SMALL_GIF,
        content_type='image/gif'
    )
    return UPLOADED


def create_audio_file():
    testfile_audio = (
        b'MM\x00*\x00\x00\x00\x08\x00\x03\x01\x00\x00\x03\x00\x00\x00\x01\x00\x01'
        b'\x00\x00\x01\x01\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01\x11\x00\x03'
        b'\x00\x00\x00\x01\x00\x00\x00\x00')
    audio_file = SimpleUploadedFile(name='music.mp3',
                                    content=testfile_audio,
                                    content_type='audio/mpeg')
    return audio_file


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


@pytest.mark.django_db()
def test_03_task_doc_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_04_task_doc_create_with_right_file_type(user_client, create_task):
    doc_file = create_text_file()
    task = create_task
    data = {'text': 'asdf',
            'doc_file': doc_file}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_05_task_doc_create_with_wrong_file_type(user_client, create_task):
    image = create_image_file()
    task = create_task
    data = {'text': 'asdf',
            'doc_file': image}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/doc/',
                                data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_06_task_image_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_07_task_image_create_with_right_file_type(user_client, create_task):
    image = create_image_file()
    task = create_task
    data = {'text': 'asdf',
            'image_file': image}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_08_task_image_create_with_wrong_file_type(user_client, create_task):
    audio = create_audio_file()
    task = create_task
    data = {'text': 'asdf',
            'image_file': audio}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/image/',
                                data=data, format='json')
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_09_task_audio_create_without_file(user_client, create_task):
    task = create_task
    data = {'text': 'asdf'}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data, format='json')
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_10_task_audio_create_with_right_file_type(user_client, create_task):
    audio = create_audio_file()
    task = create_task
    data = {'text': 'asdf',
            'audio_file': audio}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data)
    print('audio: ', audio)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_11_task_audio_create_with_wrong_file_type(user_client, create_task):
    doc_file = create_text_file()
    task = create_task
    data = {'text': 'asdf',
            'audio_file': doc_file}
    response = user_client.post(f'/v1/tasks/task/{task["id"]}/audio/',
                                data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_12_comment_doc_create_without_file(user_client, create_comment):
    task, comment = create_comment
    data = {'text': 'asdf'}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_13_comment_doc_create_with_file(user_client, create_comment):
    doc_file = create_text_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'doc_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_14_comment_doc_create_with_wrong_file_type(user_client, create_comment):
    image = create_image_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'doc_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/doc/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_15_comment_image_create_without_file(user_client, create_comment):
    task, comment = create_comment
    data = {'text': 'asdf'}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_16_comment_image_create_with_file(user_client, create_comment):
    image = create_image_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'image_file': image}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_17_comment_image_create_with_wrong_file_type(user_client, create_comment):
    doc_file = create_text_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'image_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/image/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'


@pytest.mark.django_db()
def test_18_comment_audio_create_without_file(user_client, create_comment):
    task, comment = create_comment
    data = {'text': 'asdf'}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/audio/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_19_comment_audio_create_with_right_file_type(user_client, create_comment):
    audio_file = create_audio_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'audio_file': audio_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/audio/',
        data=data)
    assert response.status_code == 201, f'{response.json()}'


@pytest.mark.django_db()
def test_20_comment_audio_create_with_wrong_file_type(user_client, create_comment):
    doc_file = create_text_file()
    task, comment = create_comment
    data = {'text': 'asdf',
            'audio_file': doc_file}
    response = user_client.post(
        f'/v1/tasks/task/{task["id"]}/comment/{comment["id"]}/audio/',
        data=data)
    assert response.status_code == 400, f'{response.json()}'
