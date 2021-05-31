from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from accounts.serializers import UserRegistrationSerializer
from tasks.models import TaskTag
from tasks.serializers import TagSerializer


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
