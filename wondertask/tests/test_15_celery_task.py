import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from django.utils.timezone import now
from django_celery_beat.models import CrontabSchedule

from journals.models import Notification
from tasks import tasks
from tasks.models import Task, TaskSchedule

User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_01_create_repeats_tasks_number_of_times(celery_app, celery_worker):
    user = User.objects.create(email="test@user.com", password="1235")
    task = Task.objects.create(
        title="title", creator=user,
        deadline=timezone.now() + timezone.timedelta(days=3)
    )
    crontab = CrontabSchedule.objects.create(minute=0, hour=0, day_of_month="*/1")
    number_of_times = 5
    TaskSchedule.objects.create(crontab=crontab, task=task, number_of_times=number_of_times)

    task_count_before = Task.objects.count()
    tasks.create_repeats_tasks(task.id)
    task_schedule = TaskSchedule.objects.get(task_id=task.id)

    assert Task.objects.count() == task_count_before + number_of_times
    assert task_schedule.periodic_tasks.filter(task="start_repeat_task").count() == number_of_times


@pytest.mark.django_db(transaction=True)
def test_02_create_repeats_tasks_end_date(celery_app, celery_worker):
    user = User.objects.create(email="test@user.com", password="1235")
    task = Task.objects.create(
        title="title", creator=user,
        deadline=timezone.now() + timezone.timedelta(days=3)
    )
    crontab = CrontabSchedule.objects.create(minute=0, hour=0, day_of_month="*/1")
    end_date = timezone.now() + timezone.timedelta(days=10)
    task_schedule = TaskSchedule.objects.create(crontab=crontab, task=task, end_date=end_date)

    # counter the number of tasks to be created
    crontab_timezone = task_schedule.crontab.timezone
    remaining_estimate = task_schedule.crontab.schedule.remaining_estimate(
        now().astimezone(crontab_timezone))
    creation_date = now().astimezone(crontab_timezone) + remaining_estimate
    counter = 0
    while True:
        counter += 1
        remaining_estimate = task_schedule.crontab.schedule.remaining_estimate(creation_date)
        creation_date = now().astimezone(crontab_timezone) + remaining_estimate
        if task_schedule.end_date and creation_date >= task_schedule.end_date or counter >= 365:
            break

    task_count_before = Task.objects.count()
    tasks.create_repeats_tasks(task_id=task.id)
    task_schedule = TaskSchedule.objects.get(task_id=task.id)

    assert Task.objects.count() == task_count_before + counter
    assert task_schedule.periodic_tasks.filter(task="start_repeat_task").count() == counter


@pytest.mark.django_db(transaction=True)
def test_03_start_repeat_task(celery_app, celery_worker):
    user = User.objects.create(email="test@user.com", password="1235")
    task = Task.objects.create(
        title="title", creator=user,
        deadline=timezone.now() + timezone.timedelta(days=3)
    )
    tasks.start_repeat_task(task_id=task.id)

    assert Task.objects.get(pk=task.pk).status == task.IN_PROGRESS


@pytest.mark.django_db(transaction=True)
def test_04_deadline_notification(celery_app, celery_worker):
    user = User.objects.create(email="test@user.com", password="1235")
    task = Task.objects.create(
        title="title", creator=user,
        deadline=timezone.now() + timezone.timedelta(days=3)
    )
    notify_count = Notification.objects.count()

    tasks.deadline_notification(task_id=task.id, hour_before_deadline=10)

    assert Notification.objects.count() == notify_count + 1


@pytest.mark.django_db(transaction=True)
def test_05_send_invite_in_group(celery_app, celery_worker):
    tasks.send_invite_in_group(
        group_name="group name",
        link="http://localhost/tasks/task/accept-invite/email=user@example.com",
        email="user@example.com",
    )
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_06_send_mail_thread(celery_app, celery_worker):
    tasks.send_mail_thread(
        url="http://localhost/",
        email="user@example.com",
    )
    assert len(mail.outbox) == 1
