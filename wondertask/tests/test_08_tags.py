import pytest


@pytest.mark.django_db()
def test_01_get_tags_list(user_client, create_tag):
    response = user_client.get(f'/v1/tasks/tags/')
    assert response.status_code == 200
    assert response.json()['results'] == [create_tag]


@pytest.mark.django_db()
def test_02_get_single_tag(user_client, create_tag):
    response = user_client.get(f'/v1/tasks/tags/{create_tag["id"]}/')
    assert response.status_code == 200
    assert response.json() == create_tag


@pytest.mark.django_db()
def test_03_tag_create(user_client):
    data = {"name": "work"}
    response = user_client.post(f'/v1/tasks/tags/', data=data)
    assert response.status_code == 201
    assert response.json()['name'] == data['name']


@pytest.mark.django_db()
def test_04_tag_delete(user_client, create_tag):
    response = user_client.delete(f'/v1/tasks/tags/{create_tag["id"]}/')
    assert response.status_code == 204


@pytest.mark.django_db()
def test_05_add_tags_to_task(user_client, create_task):
    data = {"tags": ["project", "work"]}
    response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/add-tags/', data=data)
    assert response.status_code == 200


@pytest.mark.django_db()
def test_06_del_tags_from_task(user_client, create_task):
    tags_del_data = {"tags": ["project"]}
    response = user_client.delete(f'/v1/tasks/task/{create_task["id"]}/del-tags/',
                                  data=tags_del_data)
    assert response.status_code == 200


@pytest.mark.django_db()
def test_07_get_user_tags_by_user_id(user_client, create_tag):
    response = user_client.get(f'/v1/accounts/user/1/tags/')
    assert response.status_code == 200
    assert response.json()['tags'] == [create_tag]
