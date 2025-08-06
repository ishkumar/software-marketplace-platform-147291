from django.contrib.auth import login, logout
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register (manual/local) user."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user)
        return Response({'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login with username/password."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'user': UserSerializer(user).data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUBLIC_INTERFACE
@api_view(['POST'])
def logout_view(request):
    """Logout currently authenticated user."""
    logout(request)
    return Response({"detail": "Logged out."}, status=status.HTTP_204_NO_CONTENT)

# PUBLIC_INTERFACE
@api_view(['GET'])
def profile(request):
    """Get the currently authenticated user's profile."""
    return Response({'user': UserSerializer(request.user).data})

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Social login/signup via Google (entry point for frontend OAuth).
    Expects an access_token from React frontend,
    handles user fetch/creation.
    """
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from dj_rest_auth.registration.views import SocialLoginView
    class GoogleLogin(SocialLoginView):
        adapter_class = GoogleOAuth2Adapter
    view = GoogleLogin.as_view()
    return view(request._request)

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([AllowAny])
def github_login(request):
    """
    Social login/signup via GitHub (entry point for frontend OAuth).
    Expects an access_token from React frontend,
    handles user fetch/creation.
    """
    from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
    from dj_rest_auth.registration.views import SocialLoginView
    class GitHubLogin(SocialLoginView):
        adapter_class = GitHubOAuth2Adapter
    view = GitHubLogin.as_view()
    return view(request._request)
