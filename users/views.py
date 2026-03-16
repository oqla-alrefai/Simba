from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth import authenticate
from .serializers import *
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid input data"})
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({
            "success": True,
            "data": {
                "user": UserSerializer(user).data,
                "token": token
            }
        })

class LoginView(APIView):
    def post(self, request):
        print("Login request data:", request.data)
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid input data"})

        # Django's default ModelBackend expects a `username` keyword, even when
        # the custom user model uses `email` as the USERNAME_FIELD.
        user = authenticate(
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )

        if not user:
            return Response({"success": False, "message": "Invalid credentials"})

        token = get_tokens_for_user(user)

        return Response({
            "success": True,
            "data": {
                "user": UserSerializer(user).data,
                "token": token
            }
        })

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "admin":
            return User.objects.none()
        return User.objects.all()