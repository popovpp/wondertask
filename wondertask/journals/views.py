from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from journals.models import Notification, NotificationToUser
from journals.serializer import NotificationSerializer, ActionReadNotificationsSerializer
from journals.services import notify_service


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all().prefetch_related("recipients").order_by("-created")
    serializer_class = NotificationSerializer

    @action(methods=["GET"], url_path="my", url_name="my", detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_my_notifications(self, request):
        queryset = self.get_queryset()
        queryset = queryset.filter(recipients__user=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(data={
                "unread": NotificationToUser.objects.filter(user=request.user,
                                                            is_read=False).count(),
                "notification": serializer.data
            })
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
