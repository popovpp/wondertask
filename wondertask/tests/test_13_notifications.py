import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db()
def test_01_get_notifications_list(user_client, create_notification):
    response = user_client.get(f'/v1/journals/notifications/')
    assert response.status_code == 200
    assert response.json()['count'] > 0


@pytest.mark.django_db()
def test_02_get_single_notification(user_client, create_notification):
    response = user_client.get(f'/v1/journals/notifications/{create_notification["id"]}/')
    assert response.status_code == 200
    assert response.json()['message'] == create_notification["message"]


@pytest.mark.django_db()
def test_03_notifications_create(user_client):
    data = {"message": "Some message"}
    response = user_client.post(f'/v1/journals/notifications/', data=data)
    assert response.status_code == 201


@pytest.mark.django_db()
def test_04_patch_notification(user_client, create_notification):
    data = {'message': '1234'}
    response = user_client.patch(f'/v1/journals/notifications/{create_notification["id"]}/',
                                 data=data)
    assert response.status_code == 200
    assert response.json()['message'] == data['message']


@pytest.mark.django_db()
def test_05_update_notification(user_client, create_notification, create_group):
    data = {'message': 'some message', 'group': create_group["id"]}
    response = user_client.put(f'/v1/journals/notifications/{create_notification["id"]}/',
                               data=data)
    assert response.status_code == 200
    assert response.json()['message'] == data['message']
    assert response.json()['group'] == data['group']


@pytest.mark.django_db()
def test_06_delete_notification(user_client, create_notification):
    response = user_client.delete(f'/v1/journals/notifications/{create_notification["id"]}/')
    assert response.status_code == 204


@pytest.mark.django_db()
def test_07_get_notifications_list_my(user_client, create_notification):
    response = user_client.get(f'/v1/journals/notifications/my/')
    assert response.status_code == 200
    assert response.json()['count'] > 0


@pytest.mark.django_db()
def test_08_read_notification(user_client, create_notification):
    response = user_client.post(f'/v1/journals/notifications/{create_notification["id"]}/read/')
    assert response.status_code == 200


@pytest.mark.django_db()
def test_09_read_bulk_notification(user_client, create_notification):
    response = user_client.post(f'/v1/journals/notifications/read/bulk/',
                                data={'notifications': [create_notification['id']]})
    assert response.status_code == 200


@pytest.mark.django_db()
def test_10_read_bulk_notification(user_client, create_notification):
    response = user_client.get(f'/v1/journals/notifications/actions-journal/')
    assert response.status_code == 200
    assert response.json()['count'] > 0
