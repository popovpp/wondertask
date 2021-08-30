from rest_framework import serializers
from django.urls import resolve

from journals.models import Notification, NotificationToUser
from tasks.services import group_service


class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    from_user_avatar = serializers.SerializerMethodField(method_name="get_user_avatar")
    is_read = serializers.SerializerMethodField(method_name="get_is_read")

    class Meta:
        model = Notification
        fields = ["id", "message", "type", "task", "group", "created", "recipients",
                  "from_user", "from_user_avatar", "is_read"]

    @staticmethod
    def get_user_avatar(instance):
        if not instance.from_user:
            return ""
        return instance.from_user.avatar_image.url if instance.from_user.avatar_image else ""

    def get_is_read(self, instance):
        user = self.context['request'].user
        reads_notifications = NotificationToUser.objects.filter(user=user, is_read=True)\
            .values_list("notification_id", flat=True)
        return True if instance.pk in reads_notifications else False

    def to_representation(self, instance):
        output_data = super().to_representation(instance)
        if not (self.context['request'] and 'actions_journal' in
                resolve(self.context['request'].path_info).url_name):
            if self.context['request'].user in [x.user for x in instance.recipients.all()]:
                output_data['message'] = output_data['message'].replace(
                    self.context['request'].user.full_name, 'Вы').replace(
                    'л(а)', 'ли').replace(
                    'перенес', 'перенесли')
        output_data["recipients"] = [obj.user.id for obj in instance.recipients.all()]
        if not instance.task:
            output_data['task'] = instance.task_id_del
        if not instance.group:
            output_data['group'] = instance.group_name_del

        user = self.context['request'].user
        if instance.type == Notification.INVITE:
            output_data['is_accepted'] = instance.group.group_members.filter(pk=user.pk).exists()
            output_data['secret'] = group_service.get_invite_token(user=user, group=instance.group)

        return output_data

    def create(self, validated_data):
        if "recipients" not in validated_data:
            notification = super(NotificationSerializer, self).create(validated_data)
        else:
            recipients = validated_data.pop("recipients")
            notification = super(NotificationSerializer, self).create(validated_data)
            notification.recipients.bulk_create(
                NotificationToUser(user_id=recipient_id, notification=notification)
                for recipient_id in recipients
            )
        if not notification.task:
            notification.task_id_del = None
        else:
            notification.task_id_del = notification.task.id
        if not notification.group:
            notification.group_name_del = None
        else:
            notification.group_name_del = notification.group.group_name
        notification.save()
        return notification


class ActionReadNotificationsSerializer(serializers.Serializer):
    notifications = serializers.ListField(child=serializers.IntegerField())
