from django.db import models
from django.utils import timezone
from taggit.managers import TaggableManager
import mptt
from mptt.fields import TreeForeignKey

from accounts.models import User


class Task(models.Model):

    CREATED = 0
    IN_PROGRESS = 1
    IN_WAITING = 2
    DONE = 4
    OVERDUE = 8
    IN_PROGRESS_OVERDUE = IN_PROGRESS + OVERDUE
    IN_WAITING_OVERDUE = IN_WAITING + OVERDUE
    STATUS_DICT = {
                   CREATED : 'CREATED',
               IN_PROGRESS : 'IN_PROGRESS',
                IN_WAITING : 'IN_WAITING',
                      DONE : 'DONE',
                   OVERDUE : 'OVERDUE',
       IN_PROGRESS_OVERDUE : 'IN_PROGRESS_OVERDUE',
        IN_WAITING_OVERDUE : 'IN_WAITING_OVERDUE'
    }

    title = models.CharField(max_length=255, default='', blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    last_start_time = models.DateTimeField(blank=True, null=True)
    sum_elapsed_time = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(default=CREATED)
    priority = models.PositiveIntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='task_authors')

    user_tags = TaggableManager()

    class Meta:
        db_table = 'tasks'

    def set_status(self):
    	pass

    def set_sum_elapsed_time(self):
    	pass


TreeForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True).contribute_to_class(Task, 'parent')
mptt.register(Task, order_insertion_by=['id'])


class TaskSystemTags(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='task_field')
    system_tags = TaggableManager()
    
    class Meta:
        db_table = 'task_system_tags'


class Executor(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='executors')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_executor')

    class Meta:
        db_table = 'executors'


class Observer(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                                related_name='observers')
    observer = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_observer')

    class Meta:
        db_table = 'observers'


class Group(models.Model):

    group_name = models.CharField(max_length=255, default='', blank=True, null=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'groups'

    def __str__(self):
        return repr(self.group_name)


class TaskGroup(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='task_group_group_field')

    class Meta:
        db_table = 'taskgroups'
        unique_together = ('task', 'group')
