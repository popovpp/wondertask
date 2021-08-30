from collections import OrderedDict

import django_filters
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from journals.models import Notification
from journals.serializers import NotificationSerializer, ActionReadNotificationsSerializer
from journals.services import notify_service


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('unread', notify_service.get_unread_notification(self.request)),
            ('results', data),
        ]))


class NotificationFilters(django_filters.FilterSet):
    keyword = django_filters.CharFilter(field_name="keyword", method='keyword_filter')

    @staticmethod
    def keyword_filter(self, queryset, name, value):
        result = {
            "new": queryset.filter(recipients__is_read=False),
            "old": queryset.filter(recipients__is_read=True),
        }
        return result.get(value, queryset)


class NotificationViewSet(ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filterset_class = NotificationFilters

    def get_queryset(self):
        return Notification.objects.filter(recipients__user=self.request.user). \
            prefetch_related("recipients").order_by("-created")

    @action(methods=["GET"], url_path="actions-journal", url_name="actions_journal", detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def actions_journal(self, request):
        queryset = self.get_queryset()
        queryset = queryset.filter(recipients__user=request.user).filter(type='ACTION')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(data=serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["POST"], url_path="read", url_name="read", detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def read(self, request, pk=None):
        notify_service.read_notification(notification_id=pk, user=request.user)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["POST"], url_path="read/bulk", url_name="read-bulk", detail=False,
            serializer_class=ActionReadNotificationsSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def read_bulk(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        notify_service.read_notifications_bulk(
            notification_list_ids=serializer.data["notifications"],
            user=request.user
        )
        return Response(status=status.HTTP_200_OK)
