from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"ok": True})


# ----------------------------------------------------
# STEP 1: SEND OTP
# ----------------------------------------------------
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        # privacy
        if not user:
            return Response(
                {"detail": "If an account exists for this email, password reset instructions were sent."}
            )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return Response(
            {
                "detail": "Password reset instructions generated.",
                "uid": uid,
                "token": token,
            }
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            email = force_str(urlsafe_base64_decode(uidb64))
        except:
            return Response({"detail": "Invalid UID."}, status=400)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"detail": "User not found."}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password updated successfully."})


# ----------------------------------------------------
# LOGOUT
# ----------------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token required."}, status=400)

        try:
            RefreshToken(refresh).blacklist()
        except:
            return Response({"detail": "Invalid refresh token."}, status=400)

        return Response({"detail": "Logged out."})
