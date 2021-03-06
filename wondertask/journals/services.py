from typing import List

from django.urls import resolve
from rest_framework.generics import get_object_or_404

from accounts.models import User
from . import tasks
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
            self._create_notification(message=message, recipients=recipients, task=task,
                                      group=group, type="ACTION")
        elif task_action:
            if request:
                full_name = request.user.full_name
            else:
                full_name = task.creator.full_name
            message = self._task_action_message(username=full_name,
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
        request = get_request()
        message = self._add_object_message(
            task=task, object_name=object_name, username=request.user.full_name
        )
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
    def get_unread_notification(request) -> int:
        return NotificationToUser.objects.filter(user=request.user, is_read=False).count()

    @staticmethod
    def _create_notification(
            message: str, type: str, recipients: List[User], task: Task = None, group: Group = None, **kwargs
    ) -> None:
        request = get_request()
        if request and request.user:
            user = request.user
        else:
            user = None

        if not task:
            task_id_del = None
        else:
            task_id_del = task.id
        if not group:
            group_name_del = None
        else:
            group_name_del = group.group_name
        if (request and resolve(request.path_info).url_name
                in ["task-detail", ]):
            task = None
        if (request and resolve(request.path_info).url_name
                in ["groups-detail", ]):
            group = None
        notification = Notification.objects.create(
            message=message, task=task, task_id_del=task_id_del,
            group=group, group_name_del=group_name_del, from_user=user
        )
        notification.recipients.bulk_create(
            NotificationToUser(user=user, notification=notification) for user in recipients
        )
        if type == "ACTION":
            notification.set_action_type()
        if type == "DEADLINE":
            notification.set_deadline_type()
        if type == "INVITE":
            notification.set_invite_type()
        notification.save()

        push_notification_data = {
            "message": notification.message,
            "notification_message": notification.message,
            "notification_id": notification.pk,
            "notification_type": notification.type
        }
        # if current user made this action, he will remove from recipients for push notifications
        if user:
            push_notification_data['from_user_id'] = user.id
            push_notification_data['from_user_av_url'] = user.avatar_image.url if user.avatar_image else ""
            try:
                recipients.remove(user)
            except ValueError:
                pass
        if group:
            push_notification_data["group_id"] = group.pk
            push_notification_data["group_name"] = group.group_name
            push_notification_data["secret"] = kwargs.get('secret', "")

        if recipients:
            user_ids = [user.id for user in recipients]
            tasks.fcm_send_message.delay(
                user_ids=user_ids, extra=push_notification_data,
            )

    @staticmethod
    def _action_message(user_name: str, method: str, task: Task) -> str:
        method_in_msg = {
            "POST": "????????????(??)",
            "PUT": "??????????????(??)",
            "PATCH": "??????????????(??)",
            "DELETE": "????????????(??)",
        }
        action = method_in_msg.get(method, Exception("Request method unknown"))
        if task.group:
            return f"{user_name} {action} ???????????? '{task.title}' ?? ???????????? '{task.group.group_name}'"
        else:
            return f"{user_name} {action} ???????????? '{task.title}'"

    @staticmethod
    def _task_action_message(username: str, task: Task, task_action: str) -> str:
        action_in_msg = {
            "start_task": "??????????(??)",
            "stop_task": "??????????????????(??)",
            "finish_task": "????????????????(??)"
        }
        action = action_in_msg.get(task_action, Exception("Task action unknown"))
        return f"{username} {action} ???????????? '{task.title}'"

    @staticmethod
    def _changed_group_message(task: Task, old_group: Group = None, new_group: Group = None) -> str:
        if old_group:
            return f"{old_group.creator.full_name} ?????????????? ???????????? '{task.title}' " \
                   f"???? ???????????? '{old_group.group_name}' ?? ???????????? '{new_group.group_name}'"
        else:
            return f"???????????? '{task.title}' ?????????????????? ?? ???????????? '{new_group.group_name}'"

    @staticmethod
    def _deadline_message(task: Task, hour_before_deadline: int) -> str:
        if hour_before_deadline == 0:
            if task.group:
                return f"???????????? '{task.title}' ???? ???????????? '{task.group.group_name}' ????????????????????"
            else:
                return f"???????????? '{task.title}' ????????????????????"

        if task.group:
            return f"?????? ???????????? '{task.title}' ???? ???????????? '{task.group.group_name}' " \
                   f"deadline ?????????????????? ?????????? {hour_before_deadline} ??????(????)"
        else:
            return f"?????? ???????????? '{task.title}' deadline ?????????????????? ?????????? {hour_before_deadline} ??????(????)"

    @staticmethod
    def _repeated_task_message(task: Task):
        if task.group:
            return f"{task.creator.full_name} ????????????(??) ?? ???????????? '{task.group.group_name}'" \
                   f" ?????????????????????????? ???????????? {task.title}"
        else:
            return f"{task.creator.full_name} ????????????(??) ?????????????????????????? ???????????? '{task.title}'"

    @staticmethod
    def _add_object_message(username: str, task: Task, object_name):
        if task.group:
            return f"{username} ??????????????(??) {object_name} ?? ???????????? '{task.title}'" \
                   f" ?? ???????????? '{task.group.group_name}'"
        else:
            return f"{username} ??????????????(??) {object_name} ?? ???????????? '{task.title}'"

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
        recipients = self._users_who_receive_notification(creator=group.creator)
        self._create_notification(
            message=message, recipients=recipients, group=group, type="ACTION"
        )

    @staticmethod
    def _add_group_message(group: Group):
        return f"{group.creator.full_name} ????????????(??) ???????????? {group.group_name}"

    @staticmethod
    def _del_group_message(group: Group):
        return f"{group.creator.full_name} ????????????(??) ???????????? {group.group_name}"

    def send_del_group_notifications(self, group: Group):
        message = self._del_group_message(group=group)
        recipients = self._users_who_receive_notification(creator=group.creator)
        self._create_notification(
            message=message, recipients=recipients, group=group, type="ACTION"
        )

    @staticmethod
    def _add_user_role_message(task: Task, role: str):
        role_in_msg = {
            "executor": "????????????????????????",
            "observer": "????????????????????????",
        }
        role = role_in_msg.get(role, Exception("Task role unknown"))
        return f"{task.creator.full_name} ?????????????? ?????? {role} ???????????? '{task.title}'"

    def send_add_user_to_task_notifications(self, task: Task, recipient: User, role: str):
        message = self._add_user_role_message(task=task, role=role)
        self._create_notification(
            message=message, task=task, recipients=[recipient], group=task.group, type="ACTION"
        )

    def send_invite_user_in_group_notifications(self, group, recipient, secret):
        message = f"{group.creator.full_name} ?????????????????? ?????? ?? ???????????? '{group.group_name}'"
        self._create_notification(
            message=message, recipients=[recipient], group=group, type="INVITE", secret=secret
        )


notify_service = NotificationService()
