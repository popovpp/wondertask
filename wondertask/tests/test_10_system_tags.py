import pytest


@pytest.mark.django_db()
def test_01_get_system_tags_list(user_client, create_system_tag):
    response = user_client.get(f'/v1/tasks/systemtags/')
    assert response.status_code == 200
    assert response.json()['results'] == [create_system_tag]


@pytest.mark.django_db()
def test_02_get_single_system_tag(user_client, create_system_tag):
    response = user_client.get(f'/v1/tasks/systemtags/{create_system_tag["id"]}/')
    assert response.status_code == 200
    assert response.json() == create_system_tag


@pytest.mark.django_db()
def test_03_system_tag_create(user_client):
    data = {"name": "РЕГУЛЯРНАЯ"}
    response = user_client.post(f'/v1/tasks/systemtags/', data=data)
    assert response.status_code == 201
    assert response.json()['name'] == data['name']


@pytest.mark.django_db()
def test_04_system_tag_delete(user_client, create_system_tag):
    response = user_client.delete(f'/v1/tasks/systemtags/{create_system_tag["id"]}/')
    assert response.status_code == 204


@pytest.mark.django_db()
def test_05_add_system_tags_to_task(user_client, create_task):
    data = {"tags": ["$регулярная", "project"]}
    response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/add-tags/', data)
    assert response.status_code == 200, response.json()


@pytest.mark.django_db()
def test_06_del_system_tags_from_task(user_client, create_task):
    tags_del_data = {"tags": ["$регулярная"]}
    response = user_client.delete(f'/v1/tasks/task/{create_task["id"]}/del-tags/',
                                  data=tags_del_data)
    assert response.status_code == 200

