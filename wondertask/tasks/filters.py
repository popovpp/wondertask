import django_filters
from django.db.models import Case, When, Value, IntegerField, Q
from django.utils import timezone

from tasks.models import Task


class TaskFilters(django_filters.FilterSet):
    creation_date = django_filters.DateFromToRangeFilter(field_name="creation_date")
    deadline = django_filters.DateFromToRangeFilter(field_name="deadline")
    start_date = django_filters.DateFromToRangeFilter(field_name="start_date")
    finish_date = django_filters.DateFromToRangeFilter(field_name="finish_date")
    tags = django_filters.CharFilter(field_name="user_tags", method='filter_tags')
    keyword = django_filters.CharFilter(field_name="keyword", method='keyword_filter')
    order = django_filters.CharFilter(field_name="order", method='order_filter')

    class Meta:
        model = Task
        fields = ["status", "priority"]

    @staticmethod
    def filter_tags(queryset, name, value):
        tags = value.replace(' ', '').upper().split(',')
        return queryset.filter(Q(user_tags__name__in=tags) |
                               Q(system_tags__name__in=tags)).distinct()

    def keyword_filter(self, queryset, name, value):
        result = {
            "creator": queryset.filter(creator=self.request.user),
            "executor": queryset.filter(executors__executor=self.request.user).exclude(creator=self.request.user),
            "observers": queryset.filter(observers__observer=self.request.user),
            "favorite": queryset.filter(favorite__executor=self.request.user),
            "today": get_today_tasks(queryset),
            "tomorrow": get_tomorrow_tasks(queryset),
            "week": get_week_tasks(queryset),
            "month": get_month_tasks(queryset),
        }
        return result.get(value.lower(), queryset)

    def order_filter(self, queryset, name, value):
        status_dict = {
            "CREATED": 1,
            "IN_PROGRESS": 2,
            "IN_WAITING": 3,
            "DONE": 4,
            "OVERDUE": 8,
            "IN_PROGRESS_OVERDUE": 9,
            "IN_WAITING_OVERDUE": 10,
        }
        status = status_dict.get(value.upper(), None)
        if status:
            return queryset.annotate(
                order=Case(
                    When(status=status, then=Value(0)),
                    output_field=IntegerField(),
                )).order_by('order', 'status')

        keyword = {
            "priority": queryset.annotate(
                order=Case(
                    When(priority=1, then=Value(0)),
                    When(priority=2, then=Value(1)),
                    When(priority=3, then=Value(2)),
                    When(priority=4, then=Value(3)),
                    When(priority=0, then=Value(4)),
                    output_field=IntegerField(),
                )).order_by('order', 'priority'),
            "today": get_today_task_ordering(queryset),
            "id": queryset.order_by('id')
        }
        return keyword.get(value.lower(), queryset)


def get_today_tasks(queryset):
    today = timezone.now().replace(hour=0, minute=0, second=0)
    tomorrow = today + timezone.timedelta(days=1)
    return queryset.filter(deadline__gte=today, deadline__lt=tomorrow)


def get_tomorrow_tasks(queryset):
    today = timezone.now().replace(hour=23, minute=59, second=59)
    tomorrow = today + timezone.timedelta(days=1)
    return queryset.filter(deadline__gt=today, deadline__lte=tomorrow)


def get_week_tasks(queryset):
    today = timezone.now().replace(hour=0, minute=0, second=0)
    week = today + timezone.timedelta(days=7)
    return queryset.filter(deadline__gte=today, deadline__lte=week)


def get_month_tasks(queryset):
    today = timezone.now().replace(hour=0, minute=0, second=0)
    month = today + timezone.timedelta(days=30)
    return queryset.filter(deadline__gte=today, deadline__lte=month)


def get_today_task_ordering(queryset):
    today = timezone.now().replace(hour=0, minute=0, second=0)
    tomorrow = today + timezone.timedelta(days=1)
    return queryset.annotate(
        order=Case(
            When(Q(deadline__gte=today) & Q(deadline__lt=tomorrow), then=Value(0)),
            output_field=IntegerField(),
        )).order_by('order', 'deadline')
