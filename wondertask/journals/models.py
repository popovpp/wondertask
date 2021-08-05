from django.db import models

from accounts.models import User
from tasks.models import Task, Group


class Notification(models.Model):
    ACTION = 'ACTION'
    DEADLINE = 'DEADLINE'
    type = models.CharField(max_length=8, default=None, null=True)
    message = models.CharField(max_length=500)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    group_name_del = models.CharField(max_length=255, default='', blank=True, null=True)
    task_id_del = models.IntegerField(null=True)

    class Meta:
        db_table = "notification"

    def set_action_type(self):
        self.type = self.ACTION

    def set_deadline_type(self):
        self.type = self.DEADLINE


class NotificationToUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_user")
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="recipients")
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_m2m_user"
