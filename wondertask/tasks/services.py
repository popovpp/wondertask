from rest_framework.generics import get_object_or_404
from taggit.models import Tag

from accounts.models import User
from tasks.tasks import send_invite_in_group
from tasks.models import Task, Group, TaskSchedule


class TagService:

    @staticmethod
    def filtering_tags(tags: list) -> tuple:
        """
        Splits tags into user tags and system tags. System tag must contains '$'
        """
        system_tag = []
        for tag_name in tags.copy():
            if '$' in tag_name:
                system_tag.append(tag_name.replace('$', ''))
                tags.remove(tag_name)
        return tags, system_tag

    @staticmethod
    def get_non_existent_system_tags(system_tag: list) -> set:
        tags_instances = Tag.objects.filter(name__in=system_tag)
        list_tags_names = [tag.name for tag in tags_instances]
        return set(system_tag) - set(list_tags_names)

    @staticmethod
    def add_tags_to_task(task_id, user_id, user_tags: list, system_tags: list) -> Task:
        task = get_object_or_404(Task, pk=task_id)
        if user_tags:
            task.user_tags.add(*user_tags, tag_kwargs={"user_id": user_id})
        if system_tags:
            task.system_tags.add(*system_tags)
        return task

    def remove_tags_from_task(self, task_id, user_tags: list, system_tags: list) -> Task:
        task = get_object_or_404(Task, pk=task_id)
        if user_tags:
            task.user_tags.remove(*user_tags)
        if system_tags:
            if "РЕГУЛЯРНАЯ" in system_tags:
                self.remove_repeated_tasks_and_task_schedule(task.id)
            task.system_tags.remove(*system_tags)
        return task

    @staticmethod
    def remove_repeated_tasks_and_task_schedule(task_id: int) -> None:
        task_schedule = TaskSchedule.objects.get(task_id=task_id)
        task_schedule.repeated_tasks.all().delete()
        task_schedule.delete()


tag_service = TagService()


class GroupService:

    @staticmethod
    def get_non_existent_user_emails(emails: list) -> set:
        users = User.objects.filter(email__in=emails)
        found_users_emails = [user.email for user in users]
        return set(emails) - set(found_users_emails)

    @staticmethod
    def invite_users_in_group(name: str, url: str, emails: list) -> None:
        for email in emails:
            send_invite_in_group.delay(group_name=name, link=f'{url}?email={email}', email=email)

    @staticmethod
    def add_user_in_group(group_id, email):
        user = get_object_or_404(User, email=email)
        group = Group.objects.get(pk=group_id)
        group.group_members.add(user)


group_service = GroupService()
