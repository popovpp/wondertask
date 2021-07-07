from rest_framework import serializers
from django.urls import resolve

from journals.models import Notification, NotificationToUser


class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(child=serializers.IntegerField(),
                                       write_only=True, required=False)

    class Meta:
        model = Notification
        fields = ["id", "message", "type", "task", "group", "created", "recipients"]

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
        return output_data

    def create(self, validated_data):
        if "recipients" not in validated_data:
            return super(NotificationSerializer, self).create(validated_data)
        recipients = validated_data.pop("recipients")
        notification = super(NotificationSerializer, self).create(validated_data)
        notification.recipients.bulk_create(
            NotificationToUser(user_id=recipient_id, notification=notification)
            for recipient_id in recipients
        )
        return notification


class ActionReadNotificationsSerializer(serializers.Serializer):
    notifications = serializers.ListField(child=serializers.IntegerField())
