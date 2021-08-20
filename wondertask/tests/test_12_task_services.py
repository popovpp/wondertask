import pytest
from django.contrib.auth import get_user_model

from tasks.models import Task, TaskSchedule, Group
from tasks.services import tag_service, group_service

User = get_user_model()


@pytest.mark.django_db()
class TestTagService:
    @pytest.mark.parametrize("all_tags, result_user_tags, result_system_tags", [
        (["work", "хобби", "$регулярная"], ["work", "хобби"], ["$регулярная"]),
        (["front", "back"], ["front", "back"], []),
        (["$регулярная", "$шаблонная"], [], ["$регулярная", "$шаблонная"]),
        ([111, 222], ['111', '222'], []),
    ])
    def test_01_filtering_tags(self, all_tags: list, result_user_tags: list,
                               result_system_tags: list):
        user_tags, system_tags = tag_service.filtering_tags(all_tags)
        assert user_tags == result_user_tags
        assert system_tags == result_system_tags

    def test_02_get_non_existent_system_tags(self, create_system_tag):
        result: set = tag_service.get_non_existent_system_tags(
            ["$тэг которого нет", create_system_tag["name"]])
        assert result == {"$тэг которого нет", }

    def test_03_add_tags_to_task(self, create_task):
        result: Task = tag_service.add_tags_to_task(task_id=create_task["id"],
                                                    user_id=create_task["creator"]['id'],
                                                    user_tags=["хобби", "проект", 44, 55],
                                                    system_tags=['$регулярная'])
        for item in ['44', '55', "ХОББИ", "ПРОЕКТ"]:
            assert item in result.user_tags.names()
        assert "$РЕГУЛЯРНАЯ" in result.system_tags.names()

    def test_04_remove_tags_from_task(self, create_task):
        res = tag_service.add_tags_to_task(task_id=create_task["id"],
                                           user_id=create_task["creator"],
                                           user_tags=["проект"],
                                           system_tags=['$шаблонная'])
        assert "ПРОЕКТ" in res.user_tags.names()
        assert "$ШАБЛОННАЯ" in res.system_tags.names()

        result: Task = tag_service.remove_tags_from_task(task_id=create_task["id"],
                                                         user_tags=["проект"],
                                                         system_tags=['$шаблонная'])
        assert "ПРОЕКТ" not in result.user_tags.names()
        assert "$ШАБЛОННАЯ" not in result.system_tags.names()

    def test_05_remove_task_schedule_and_remove_m2m_related_obj(self, create_schedule_task):
        assert TaskSchedule.objects.filter(pk=create_schedule_task["id"]).exists()
        tag_service.remove_task_schedule_and_remove_m2m_related_obj(
            task_id=create_schedule_task['task'])
        assert not TaskSchedule.objects.filter(pk=create_schedule_task["id"]).exists()


@pytest.mark.django_db()
class TestGroupService:
    def test_01_get_non_existent_user_emails(self, create_user):
        result: set = group_service.get_non_existent_user_emails(
            [create_user.email, "non@existent.user"]
        )
        assert "non@existent.user" in result

