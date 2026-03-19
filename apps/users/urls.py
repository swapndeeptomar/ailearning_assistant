from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, GoogleLoginView, GithubLoginView, CreateRazorpayOrderView, VerifyPaymentView, RazorpayWebhookView, CurrentUserView

urlpatterns = [
    path('me/', CurrentUserView.as_view(), name='current_user'),
    # Registration endpoint
    path('register/', RegisterView.as_view(), name='register'),
    
    # Standard Email/Password Login (Returns JWT Access & Refresh tokens)
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Endpoint to refresh an expired access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Social Login Endpoints
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('auth/github/', GithubLoginView.as_view(), name='github_login'),

    # Billing Endpoints
    path('billing/create-order/', CreateRazorpayOrderView.as_view(), name='create_order'),
    path('billing/verify-payment/', VerifyPaymentView.as_view(), name='verify_payment'),
    path('billing/webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
]