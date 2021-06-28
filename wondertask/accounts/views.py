import socket
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from taggit.models import Tag
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from http import HTTPStatus

from tasks.models import TaskTag
from tasks.serializers import TagSerializer
from accounts.serializers import (UserRegistrationSerializer, UserTaskSerializer, 
                                  AvatarSerializer, UserSendEmailSerializer,
                                  NewPasswordSerializer)
from accounts.models import User
from accounts.signals import avatar_delete
from tasks.tasks import send_mail_thread


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
    system_tags = [f'${tag.name}' for tag in Tag.objects.all()]
    return Response(data={"tags": serializer.data, "system_tags": system_tags}, status=200)


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserTaskSerializer
    permission_classes = [AllowAny]

    def update(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(User, id=self.kwargs['pk'])
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

    @action(methods=['GET'], detail=False, url_path="get-user", url_name="get_user",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def get_user(self, request, **kwargs):
        if 'email' not in request.query_params:
            return Response(data={"detail": "email query param is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        email = request.query_params['email']
        user = get_object_or_404(User, email=email)
        serializer = UserTaskSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSendEmailView(APIView):
    permission_classes = [AllowAny]
    
    def get_recover_password_url(self, request, user):
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        PORT = request.get_port()
        recover_password_url = (f'http://{settings.DOMAIN}' + ':' + PORT + 
                                '/v1/accounts/newpassword/' + user.secret_set() + '/')
        return recover_password_url


    def post(self, request):            

        serializer = UserSendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email=serializer.data['email'])
        if user.is_active:
            url = self.get_recover_password_url(request, user)
            try:
                send_mail_thread.delay(url, user.email)
            except Exception as e:
                print(f'Letter was not send to user {user.email}', e)
                return Response({'result': f'The letter is not send to {user.email}'}, 
                                      status=HTTPStatus.INTERNAL_SERVER_ERROR)
        else:
            return Response({'result': 'The user is not active'}, 
                                status=HTTPStatus.INTERNAL_SERVER_ERROR)
            
        return Response({'secret': f'{user.secret}', 'result': f'The letter send to {user.email}'}, 
                        status=HTTPStatus.OK)


class RedirectUserView(APIView):
    permission_classes = [AllowAny]

    def get_enter_email_url(self, request):
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        PORT = request.get_port()
        enter_email_url = ('http://178.154.203.204' + ':' + '3000' +
                           '/restore-password')
        return enter_email_url

    def get_enter_password_url(self, request, secret):
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        PORT = request.get_port()
        enter_password_url = ('http://78.154.203.204' + ':' + '3000' +
                              '/new-password/' + secret)
        return enter_password_url

    def get(self, request, **kwargs):
        secret = kwargs['secret']
        try:
            user = User.objects.get(secret=secret)
        except User.DoesNotExist:
            return HttpResponseRedirect(self.get_enter_email_url(request))
        print(self.get_enter_password_url(request, secret))
        return HttpResponseRedirect(self.get_enter_password_url(request, secret))

    def post(self, request, **kwargs):
        serializer = NewPasswordSerializer(data=request.data)
        secret = kwargs['secret']
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(secret=secret)
        except User.DoesNotExist:
            return Response({'result': 'The secret is not valid.'}, 
                            status=HTTPStatus.BAD_REQUEST)
        user.set_password(serializer.data['password'])
        user.secret_clear()
        user.save()
        return Response({'result': 'The password changed'}, 
                        status=HTTPStatus.OK)
