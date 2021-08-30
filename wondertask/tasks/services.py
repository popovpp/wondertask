import base64

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from taggit.models import Tag

from accounts.models import User
from journals.services import notify_service
from tasks.tasks import send_invite_in_group
from tasks.models import Task, Group, TaskSchedule, InvitationInGroup


class TagService:

    @staticmethod
    def filtering_tags(tags: list) -> tuple:
        """
        Splits tags into user tags and system tags. System tag must contains '$'
        """
        system_tag = []
        tags = list(map(str, tags))
        for tag_name in tags.copy():
            if '$' in tag_name:
                system_tag.append(tag_name)
                tags.remove(tag_name)
        return tags, system_tag

    @staticmethod
    def get_non_existent_system_tags(system_tag: list) -> set:
        tags_instances = Tag.objects.filter(name__in=system_tag)
        list_tags_names = [tag.name for tag in tags_instances]
        return set(system_tag) - set(list_tags_names)

    @staticmethod
    def add_tags_to_task(task_id, user_id, user_tags: list = None, system_tags: list = None) -> Task:
        task = get_object_or_404(Task, pk=task_id)
        if user_tags:
            task.user_tags.add(*list(map(str, user_tags)), tag_kwargs={"user_id": user_id})
        if system_tags:
            task.system_tags.add(*list(map(str, system_tags)))
        return task

    def remove_tags_from_task(self, task_id, user_tags: list, system_tags: list) -> Task:
        user_tags = list(map(lambda x: x.upper(), user_tags))
        system_tags = list(map(lambda x: x.upper(), system_tags))
        task = get_object_or_404(Task, pk=task_id)
        if user_tags:
            task.user_tags.remove(*user_tags)
        if system_tags:
            if "$РЕГУЛЯРНАЯ" in system_tags:
                self.remove_task_schedule_and_remove_m2m_related_obj(task.id)
            task.system_tags.remove(*system_tags)
        return task

    @staticmethod
    def remove_task_schedule_and_remove_m2m_related_obj(task_id: int) -> None:
        task_schedule = get_object_or_404(TaskSchedule, task_id=task_id)
        task_schedule.repeated_tasks.all().delete()
        task_schedule.periodic_tasks.all().delete()
        task_schedule.delete()


tag_service = TagService()


class GroupService:

    @staticmethod
    def get_non_existent_user_emails(emails: list) -> set:
        users = User.objects.filter(email__in=emails)
        found_users_emails = [user.email for user in users]
        return set(emails) - set(found_users_emails)

    @staticmethod
    def invite_users_in_group(group: Group, url: str, emails: list) -> None:
        for user in User.objects.filter(email__in=emails):
            invitation_token, _ = InvitationInGroup.objects.get_or_create(user=user, group=group)
            token = base64.urlsafe_b64encode(str(invitation_token.id).encode()).decode()
            notify_service.send_invite_user_in_group_notifications(group=group, recipient=user, secret=token)
            send_invite_in_group.delay(group_name=group.group_name, link=f'{url}?secret={token}', email=user.email)

    @staticmethod
    def accept_invite_in_group(request):
        try:
            invitation_token = request.query_params.get('secret')
            decoded_token = base64.urlsafe_b64decode(invitation_token.encode()).decode()
            invite = get_object_or_404(InvitationInGroup, id=decoded_token)
        except Exception as e:
            raise serializers.ValidationError({'detail': 'Invalid Invitation Token'})
        if not request.user.is_authenticated:
            raise serializers.ValidationError({'detail': 'Please sign in and try again'})

        group = Group.objects.get(pk=invite.group_id)
        if invite.is_multiple and request.user.is_authenticated:
            group.group_members.add(request.user)
        elif not invite.is_multiple and invite.user:
            group.group_members.add(invite.user)
            invite.delete()
        else:
            raise serializers.ValidationError({'detail': 'Something went wrong :('})

    @staticmethod
    def get_invite_token(group: Group, user) -> str:
        try:
            invitation_token = InvitationInGroup.objects.get(user=user, group=group)
        except InvitationInGroup.DoesNotExist:
            return ""
        return base64.urlsafe_b64encode(str(invitation_token.id).encode()).decode()


group_service = GroupService()
