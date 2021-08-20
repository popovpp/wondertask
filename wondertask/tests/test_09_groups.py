import base64

import pytest

from tasks.models import InvitationInGroup


@pytest.mark.django_db()
def test_01_get_group_list(user_client, create_group):
    response = user_client.get(f'/v1/tasks/groups/')
    assert response.status_code == 200
    assert response.json()['results'][0]['group_name'] == create_group["group_name"]


@pytest.mark.django_db()
def test_02_get_single_group(user_client, create_group):
    response = user_client.get(f'/v1/tasks/groups/{create_group["id"]}/')
    assert response.status_code == 200
    assert response.json()['group_name'] == create_group["group_name"]


@pytest.mark.django_db()
def test_03_group_create(user_client):
    data = {"group_name": "new some group"}
    response = user_client.post(f'/v1/tasks/groups/', data=data)
    assert response.status_code == 201
    assert response.json()['group_name'] == data['group_name']


@pytest.mark.django_db()
def test_04_group_delete(user_client, create_group):
    response = user_client.delete(f'/v1/tasks/groups/{create_group["id"]}/')
    assert response.status_code == 204


@pytest.mark.django_db()
def test_05_invite_users_in_group(user_client, create_group, create_user):
    data = {"users_emails": [create_user.email]}
    response = user_client.post(f'/v1/tasks/groups/{create_group["id"]}/invite/', data=data)
    assert response.status_code == 200


@pytest.mark.django_db()
def test_06_invalid_invite_users_in_group(user_client, create_group):
    data = {"users_emails": ["not_existing_user@gmail.com"]}
    response = user_client.post(f'/v1/tasks/groups/{create_group["id"]}/invite/', data=data)
    assert response.status_code == 400


@pytest.mark.django_db()
def test_07_accept_group_invite(user_client, create_group, create_user):
    invitation = InvitationInGroup.objects.create(user=create_user, group_id=create_group['id'])
    token = base64.urlsafe_b64encode(str(invitation.id).encode()).decode()
    response = user_client.get(
        f'/v1/tasks/groups/accept-invite/?secret={token}'
    )
    group = user_client.get(f'/v1/tasks/groups/{create_group["id"]}/').json()
    assert create_user.id in group["group_members"]
    assert response.status_code == 200, response.json()
