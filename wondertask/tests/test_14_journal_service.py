import pytest

from journals.models import Notification, NotificationToUser
from journals.services import notify_service
from tasks.models import Task, Group


@pytest.mark.django_db
class TestJournalService:
    @pytest.mark.parametrize("task_action", [
        (None,),
        ("start_task",),
        ("stop_task",),
        ("finish_task",),
    ])
    def test_01_send_notification(self, task_action, create_task):
        task = Task.objects.get(pk=create_task['id'])
        notification_count_before = Notification.objects.count()
        notify_service.send_notification(task=task, task_action=task_action)
        recipients = notify_service._users_who_receive_notification(creator=task.creator,
                                                                    executors=task.executors.all(),
                                                                    observers=task.observers.all())
        assert NotificationToUser.objects.filter(user__in=recipients,
                                                 notification__task_id=task.id)
        assert Notification.objects.count() == notification_count_before + 1

    def test_02_send_changed_group_notification(self, create_task, create_group, create_user):
        task = Task.objects.get(pk=create_task['id'])
        previous_task = task
        previous_task.group_id = create_group['id']
        recipients = notify_service._users_who_receive_notification(
            creator=task.creator,
            group_members=previous_task.group.group_members.all()
        )
        group = Group.objects.create(group_name="group_name", creator=create_user)
        task.group = group
        recipients.extend(notify_service._users_who_receive_notification(
            creator=task.creator,
            group_members=previous_task.group.group_members.all(),
            executors=task.executors.all(),
            observers=task.observers.all()
        ))
        notification_count_before = Notification.objects.count()
        notify_service.send_changed_group_notification(task=task, previous_task=previous_task)

        assert NotificationToUser.objects.filter(user__in=recipients,
                                                 notification__task_id=task.id)
        assert Notification.objects.count() == notification_count_before + 2

    def test_03_send_repeated_task_notification(self, create_task):
        task = Task.objects.get(pk=create_task['id'])
        notification_count_before = Notification.objects.count()
        notify_service.send_repeated_task_notification(task=task)
        recipients = notify_service._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )
        assert NotificationToUser.objects.filter(user__in=recipients,
                                                 notification__task_id=task.id)
        assert Notification.objects.count() == notification_count_before + 1

    def test_04_send_add_object_notifications(self, create_task, user_client, create_user):
        task = Task.objects.get(pk=create_task['id'])
        notification_count_before = Notification.objects.count()
        data = {'author': create_user.id, 'text': 'Comment for task'}
        response = user_client.post(f'/v1/tasks/task/{create_task["id"]}/comment/', data=data)

        recipients = notify_service._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )
        assert response.status_code == 201
        assert NotificationToUser.objects.filter(user__in=recipients,
                                                 notification__task_id=task.id)
        assert Notification.objects.count() == notification_count_before + 1

    def test_05_send_add_group_notifications(self, create_group):
        group = Group.objects.get(pk=create_group['id'])
        notification_count_before = Notification.objects.count()
        notify_service.send_add_group_notifications(group=group)
        recipients = notify_service._users_who_receive_notification(
            creator=group.creator,
        )
        assert NotificationToUser.objects.filter(user__in=recipients,
                                                 notification__group_id=group.id)
        assert Notification.objects.count() == notification_count_before + 1

    def test_06_read_notifications_bulk(self, create_user):
        notification_list_ids = [
            notify.notification_id for notify in NotificationToUser.objects.filter(user=create_user)
        ]
        notify_service.read_notifications_bulk(notification_list_ids=notification_list_ids,
                                               user=create_user)
        read_notify = NotificationToUser.objects.filter(notification_id__in=notification_list_ids)
        for item in read_notify:
            assert item.is_read is True

    def test_07_read_notification(self, create_notification, create_user):
        notify_service.read_notification(notification_id=create_notification['id'],
                                         user=create_user)
        read_notify = NotificationToUser.objects.get(notification_id=create_notification['id'])
        assert read_notify.is_read is True

    def test_08_create_notification(self, create_task):
        task = Task.objects.get(pk=create_task['id'])
        recipients = notify_service._users_who_receive_notification(
            creator=task.creator,
        )
        notify_count_before = Notification.objects.count()
        recipients_count_before = NotificationToUser.objects.count()
        notify_service._create_notification(message="message", task=task, recipients=recipients,
                                            type="ACTION")
        assert Notification.objects.count() == notify_count_before + 1
        assert NotificationToUser.objects.count() == recipients_count_before + 1
