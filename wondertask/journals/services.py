from typing import List

from django.urls import resolve
from rest_framework.generics import get_object_or_404

from accounts.models import User
from journals.models import Notification, NotificationToUser
from tasks.models import Executor, Observer, Task, Group


def get_request():
    import inspect
    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            return frame_record[0].f_locals['request']
    else:
        return None


class NotificationService:
    def send_notification(self, task: Task, task_action: str = None) -> None or Exception:
        request = get_request()
        recipients = self._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )

        if (request and resolve(request.path_info).url_name 
                                in ["task-list", "task-detail"]) and not task_action:
            message = self._action_message(user_name=request.user.full_name,
                                           method=request.method,
                                           task=task)
            group = task.group
            if request.method == "DELETE":
                task = None
            self._create_notification(message=message, recipients=recipients, task=task,
                                      group=group, type="ACTION")
        elif task_action:
            if request:
                user_name = request.user.full_name
            else:
                user_name = task.creator.full_name
            message = self._task_action_message(user_name=user_name,
                                                task_action=task_action,
                                                task=task)
            self._create_notification(message=message, recipients=recipients, task=task,
                                      group=task.group, type="ACTION")
        else:
            return Exception("Invalid request path or task action")

    def send_changed_group_notification(self, task: Task, previous_task: Task) -> None:
        # send notification for OLD group members
        if bool(previous_task.group):
            message = self._changed_group_message(task=task, old_group=previous_task.group,
                                                  new_group=task.group)
            recipients = self._users_who_receive_notification(
                creator=previous_task.creator,
                group_members=previous_task.group.group_members.all(),
            )
            self._create_notification(message=message, task=task, recipients=recipients,
                                      group=task.group, type="ACTION")

        # send notification for NEW group members
        message = self._changed_group_message(task=task, new_group=task.group)
        recipients = self._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all(),
        )
        self._create_notification(message=message, task=task, recipients=recipients,
                                  group=task.group, type="ACTION")

    def send_deadline_task_notification(self, task: Task, hour_before_deadline: int) -> None:
        message = self._deadline_message(task=task, hour_before_deadline=hour_before_deadline)
        recipients = self._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )
        self._create_notification(message=message, task=task, recipients=recipients,
                                  group=task.group, type="DEADLINE")

    def send_repeated_task_notification(self, task: Task):
        message = self._repeated_task_message(task=task)
        recipients = self._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )
        self._create_notification(message=message, task=task, recipients=recipients,
                                  group=task.group, type="ACTION")

    def send_add_object_notifications(self, task: Task, object_name: str):
        message = self._add_object_message(task=task, object_name=object_name)
        recipients = self._users_who_receive_notification(
            creator=task.creator,
            executors=task.executors.all(),
            observers=task.observers.all(),
            group_members=task.group.group_members.all() if task.group else None
        )
        self._create_notification(message=message, task=task, recipients=recipients,
                                  group=task.group, type="ACTION")

    @staticmethod
    def read_notifications_bulk(notification_list_ids: int, user: User) -> None:
        notifications_m2m_users = NotificationToUser.objects.filter(
            notification_id__in=notification_list_ids, user=user)
        for obj in notifications_m2m_users:
            obj.is_read = True
        NotificationToUser.objects.bulk_update(notifications_m2m_users, ['is_read'])

    @staticmethod
    def read_notification(notification_id: int, user: User) -> None:
        notify = get_object_or_404(NotificationToUser, notification_id=notification_id, user=user)
        notify.is_read = True
        notify.save()

    @staticmethod
    def _create_notification(message: str, type: str, recipients: List[User], task: Task = None,
                             group: Group = None) -> None:
        notification = Notification.objects.create(message=message, task=task, group=group)
        notification.recipients.bulk_create(
            NotificationToUser(user=user, notification=notification) for user in recipients
        )
        if type == "ACTION":
            notification.set_action_type()
        if type == "DEADLINE":
            notification.set_deadline_type()
        notification.save()

    @staticmethod
    def _action_message(user_name: str, method: str, task: Task) -> str or Exception:
        if method == "POST":
            action = "создал(а)"
        elif method in ["PUT", "PATCH"]:
            action = "обновил(а)"
        elif method == "DELETE":
            action = "удалил(а)"
        else:
            return Exception("Request method unknown")

        if task.group:
            return f"{user_name} {action} задачу '{task.title}' в группе '{task.group.group_name}'"
        else:
            return f"{user_name} {action} задачу '{task.title}'"

    @staticmethod
    def _task_action_message(user_name: str, task: Task, task_action: str) -> str or Exception:
        if task_action == "start_task":
            action = "начал(а)"
        elif task_action == "stop_task":
            action = "остановил(а)"
        elif task_action == "finish_task":
            action = "завершил(а)"
        else:
            return Exception("Task action unknown")
        return f"{user_name} {action} задачу '{task.title}'"

    @staticmethod
    def _changed_group_message(task: Task, old_group: Group = None, new_group: Group = None) -> str:
        if old_group:
            return f"{old_group.creator.full_name} перенес задачу '{task.title}' " \
                   f"из группы '{old_group.group_name}' в группу '{new_group.group_name}'"
        else:
            return f"Задача '{task.title}' добавлена в группу '{new_group.group_name}'"

    @staticmethod
    def _deadline_message(task: Task, hour_before_deadline: int) -> str:
        if hour_before_deadline == 0:
            if task.group:
                return f"Задача '{task.title}' из группы '{task.group.group_name}' просрочена"
            else:
                return f"Задача '{task.title}' просрочена"

        if task.group:
            return f"Для задачи '{task.title}' из группы '{task.group.group_name}' " \
                   f"deadline наступает через {hour_before_deadline} час(ов)"
        else:
            return f"Для задачи '{task.title}' deadline наступает через {hour_before_deadline} час(ов)"

    @staticmethod
    def _repeated_task_message(task: Task):
        if task.group:
            return f"{task.creator.full_name} создал в группе '{task.group.group_name}'" \
                   f" повторяющуюся задачу {task.title}"
        else:
            return f"{task.creator.full_name} создал повторяющаяся задача '{task.title}'"

    @staticmethod
    def _add_object_message(task: Task, object_name):
        if task.group:
            return f"{task.creator.full_name} добавил {object_name} к задаче '{task.title}'" \
                   f" в группе '{task.group.group_name}'"
        else:
            return f"{task.creator.full_name} добавил {object_name} к задаче '{task.title}'" \

    @staticmethod
    def _users_who_receive_notification(creator: User = None,
                                        executors: List[Executor] = None,
                                        observers: List[Observer] = None,
                                        group_members: List[User] = None
                                        ) -> List[User]:
        recipient = []
        if creator:
            recipient.append(creator)
        if executors:
            recipient.extend(User.objects.filter(
                pk__in=[executor.executor.id for executor in executors])
            )
        if observers:
            recipient.extend(User.objects.filter(
                pk__in=[observer.observer.id for observer in observers])
            )
        if group_members:
            recipient.extend(group_members)
        return list(set(recipient))

    def send_add_group_notifications(self, group: Group):
        message = self._add_group_message(group=group)
        recipients = self._users_who_receive_notification(
            creator=group.creator)
        self._create_notification(message=message, recipients=recipients,
                                  group=group, type="ACTION")

    @staticmethod
    def _add_group_message(group: Group):
        return f"{group.creator.full_name} создал группу {group.group_name}"


notify_service = NotificationService()
