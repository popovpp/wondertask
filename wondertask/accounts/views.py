import base64
import socket

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from taggit.models import Tag
from django.conf import settings
from django.http import HttpResponseRedirect
from http import HTTPStatus

from tasks.models import TaskTag, InvitationInGroup, Group
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
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['$full_name', '$email']

    def update(self, request, pk=None, *args, **kwargs):
        user = get_object_or_404(User, id=self.kwargs['pk'])
        serializer = UserTaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if request.method == 'PUT':
            try:
                request.data['avatar_image']
                avatar_delete(User, instance=user)
            except KeyError:
                pass
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
                                '/password-reset/' + user.secret_set() + '/')
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

        return Response({'result': f'The letter send to {user.email}'},
                        status=HTTPStatus.OK)


class RedirectUserView(APIView):
    permission_classes = [AllowAny]

    def get_enter_email_url(self, request):
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        PORT = request.get_port()
        enter_email_url = (settings.ENTER_EMAIL_URL)
        return enter_email_url

    def get_enter_password_url(self, request, secret):
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        PORT = request.get_port()
        enter_password_url = (settings.ENTER_PASSWORD_URL + secret)
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


# Все что ниже это временное решение. Убрать когда появится фронт
class RecoverPassword(forms.Form):
    new_password = forms.CharField(label='New password', max_length=40)
    repeat_password = forms.CharField(label='Repeat password', max_length=40)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=40)
    password = forms.CharField(label='Password', max_length=40)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account created! Now you can sign in!')
            return redirect('login')
        else:
            messages.warning(request, form.errors)
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,
                                username=cd['email'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.GET.get("next", False):
                        return redirect(request.GET.get("next", "login"))
                    messages.success(request, 'Authenticated successfully!')
                else:
                    messages.warning(request, 'Disabled account!')
            else:
                messages.warning(request, 'Invalid login!')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def accept_invite_link(request):
    try:
        invitation_token = request.GET.get('secret')
        decoded_token = base64.urlsafe_b64decode(invitation_token.encode()).decode()
        invite = get_object_or_404(InvitationInGroup, id=decoded_token)
        group = Group.objects.get(pk=invite.group_id)
        message = f'You have been invited to "{group.group_name}" ' \
                  f'by {invite.from_user.full_name if invite.from_user.full_name else invite.from_user.email}'

        if request.method == 'POST':
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login first and then accept the invitation!')
                return redirect('/login/?next=/accept-invite/?secret=' + invitation_token)
            if invite.is_multiple and request.user.is_authenticated:
                group.group_members.add(request.user)
                messages.success(request, 'You accept invite in group!')
            elif not invite.is_multiple and invite.user and invite.user == request.user:
                group.group_members.add(invite.user)
                messages.success(request, 'You accept invite in group!')
                invite.delete()
            else:
                messages.warning(request, 'Invalid invitation token or invite link not intended for you!')

    except Exception as e:
        messages.warning(request, 'Invalid Invitation Token!')
        return render(request, 'accept_invite.html')
    return render(request, 'accept_invite.html', context={"message": message})


def recover_password(request, secret):
    if request.method == 'POST':
        form = RecoverPassword(request.POST)
        if form.is_valid():
            if form.cleaned_data['new_password'] != form.cleaned_data['repeat_password']:
                messages.add_message(request, messages.WARNING, 'Passwords do not match!')
                form = RecoverPassword()
                return render(request, 'accounts/password_reset.html', {'form': form})
            try:
                user = User.objects.get(secret=secret)
                user.set_password(form.cleaned_data['new_password'])
                user.secret_clear()
                user.save()
                messages.add_message(request, messages.SUCCESS, 'Password changed!')
            except Exception:
                messages.add_message(request, messages.WARNING, 'Token is invalid!')
    else:
        form = RecoverPassword()
    return render(request, 'accounts/password_reset.html', {'form': form})
