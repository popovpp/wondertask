from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from tasks.models import TaskTag
from tasks.serializers import TagSerializer
from accounts.serializers import UserRegistrationSerializer, UserTaskSerializer, AvatarSerializer
from accounts.models import User
from accounts.signals import avatar_delete


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_tags(request, user_id):
    serializer = TagSerializer(data=TaskTag.objects.filter(user_id=user_id), many=True)
    serializer.is_valid()
    return Response(data=serializer.data, status=200)

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserTaskSerializer
    permission_classes = [AllowAny]

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(User, id=self.kwargs['pk'])
        print(self.kwargs['pk'])
        avatar_delete(User, instance=instance)
        return super(UserViewSet, self).update(request, pk, args, kwargs)

    @action(methods=['DELETE'], detail=True, url_path="del-avatar", url_name="del_avatar",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def del_avatar(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        avatar_delete(User, instance=user)
        user.avatar_image = None
        user.save()
        serializer = UserTaskSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
