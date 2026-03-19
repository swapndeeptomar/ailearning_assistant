import logging
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
from .services import handle_oauth_user

logger = logging.getLogger(__name__)
User = get_user_model()

from rest_framework.permissions import IsAuthenticated

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user is automatically populated by Django because of the JWT!
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ==========================================
# STANDARD CREDENTIAL AUTHENTICATION
# ==========================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [AnonRateThrottle] # Added rate limiting here too for security!

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            "message": "User registered successfully.",
            "user": UserSerializer(user, context=self.get_serializer_context()).data
        }, status=status.HTTP_201_CREATED)


# ==========================================
# OAUTH (GOOGLE & GITHUB) AUTHENTICATION
# ==========================================

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({"error": "Google token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            
            if not idinfo.get("email_verified"):
                return Response({"error": "Google email is not verified"}, status=status.HTTP_400_BAD_REQUEST)
                
            email = idinfo.get('email')
            base_username = email.split('@')[0]
            avatar_url = idinfo.get('picture')

            user, tokens = handle_oauth_user(email, 'google', base_username, avatar_url)
            
            return Response({
                "message": "Google login successful",
                "tokens": tokens,
                "user": {"id": user.id, "email": user.email, "username": user.username, "avatar_url": user.avatar_url}
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Invalid Google token attempt: {e}")
            return Response({"error": "Invalid token or data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected Google OAuth error: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GithubLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({"error": "Authorization code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Exchange the code for an Access Token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            # If you specified a redirect_uri in your frontend, you MUST include the exact same one here
            "redirect_uri": "http://localhost:5174/login" 
        }
        headers = {"Accept": "application/json"}
        
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_json = token_response.json()
        
        if "error" in token_json:
            return Response({"error": token_json.get("error_description", "Invalid GitHub code")}, status=status.HTTP_400_BAD_REQUEST)
            
        access_token = token_json.get("access_token")

        # 2. Use the Access Token to get the user's primary email
        # We fetch emails explicitly because users often hide their email on their public GitHub profile
        emails_url = "https://api.github.com/user/emails"
        email_headers = {"Authorization": f"Bearer {access_token}"}
        
        emails_response = requests.get(emails_url, headers=email_headers)
        emails_data = emails_response.json()
        
        # ==========================================
        # THE FIX: Catch GitHub API Errors Gracefully
        # ==========================================
        # If GitHub sent back an error dictionary instead of a list
        if isinstance(emails_data, dict) and "message" in emails_data:
            return Response(
                {"error": f"GitHub API rejected the token. Reason: {emails_data.get('message')}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Ensure it is actually a list before we loop
        if not isinstance(emails_data, list):
            return Response(
                {"error": "GitHub returned an unexpected format."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # ==========================================

        # Find the primary, verified email
        primary_email = None
        for email_obj in emails_data:
            if email_obj.get("primary") and email_obj.get("verified"):
                primary_email = email_obj.get("email")
                break
                
        if not primary_email:
            return Response({"error": "No verified primary email found on this GitHub account."}, status=status.HTTP_400_BAD_REQUEST)

        # ==========================================
        # NEW: Fetch the User's Public Profile (Avatar)
        # ==========================================
        profile_url = "https://api.github.com/user"
        profile_response = requests.get(profile_url, headers=email_headers)
        profile_data = profile_response.json()
        
        avatar_url = profile_data.get("avatar_url", "")

        # ==========================================
        # NEW: Create or Update the User Securely
        # ==========================================
        try:
            user, created = User.objects.get_or_create(
                email=primary_email,
                defaults={
                    'username': primary_email.split('@')[0],
                    'provider': 'github',       # <-- Track the login source
                    'avatar_url': avatar_url    # <-- Save the profile picture
                }
            )
            
            if created:
                # CRITICAL SECURITY: Lock the password field so standard login fails
                user.set_unusable_password()
                user.credits = 10
                user.save()
            else:
                # If the user already exists, let's update their avatar just in case it changed
                user.avatar_url = avatar_url
                # If they originally signed up via email but just used GitHub, link the provider
                if not getattr(user, 'provider', None):
                    user.provider = 'github'
                user.save()

            # Generate JWT Tokens for your React App
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "GitHub login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "email": user.email,
                    "credits": user.credits,
                    "avatar_url": user.avatar_url # Send the avatar to React so you can show it in the Navbar!
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
import razorpay
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Transaction

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_type = request.data.get('plan_type') # 'BASIC' or 'PRO'
        
        # Prices in paise (₹200 = 20000 paise)
        plan_prices = {
            'BASIC': 200 * 100,
            'PRO': 500 * 100
        }

        if plan_type not in plan_prices:
            return Response({"error": "Invalid plan selected."}, status=status.HTTP_400_BAD_REQUEST)

        amount = plan_prices[plan_type]

        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        }
        
        try:
            # 1. Ask Razorpay for an Order ID
            razorpay_order = razorpay_client.order.create(data=order_data)
            
            # 2. Save pending transaction cleanly
            Transaction.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order['id'],
                amount=amount / 100, # Store actual rupees in DB
                plan_type=plan_type, # Save the plan requested!
                status='PENDING'
            )
            
            return Response({
                "order_id": razorpay_order['id'],
                "amount": amount,
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID 
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Razorpay Order Creation Failed: {e}")
            return Response({"error": "Failed to create payment order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            # 1. Verify cryptographic signature to block hackers
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # 2. Find the exact order
            transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
            
            if transaction.status == 'SUCCESS':
                return Response({"message": "Payment already processed"}, status=status.HTTP_200_OK)

            # 3. Update Transaction securely
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = 'SUCCESS'
            transaction.save()

            # 4. Update User Profile & Credits securely based on DB value, NOT frontend input
            user = request.user
            user.subscription_plan = transaction.plan_type
            
            if transaction.plan_type == 'BASIC':
                user.credits += 500  # ₹200 gives 500 credits
            elif transaction.plan_type == 'PRO':
                user.credits += 2000 # ₹500 gives 2000 credits
                
            user.save()

            return Response({
                "message": "Payment successful! Credits added.",
                "new_balance": user.credits,
                "plan": user.subscription_plan
            }, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            logger.warning(f"Invalid Payment Signature for Order: {razorpay_order_id}")
            return Response({"error": "Payment verification failed. Invalid Signature."}, status=status.HTTP_400_BAD_REQUEST)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

# # Webhook for payment capture events
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    # We remove IsAuthenticated because Razorpay's server is making the request, not a logged-in user!
    permission_classes = [] 

    def post(self, request):
        # The raw body is required for signature verification
        webhook_body = request.body.decode('utf-8')
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        
        # You will get this secret from the Razorpay Dashboard in Step 3
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET 

        try:
            # 1. Verify this request actually came from Razorpay
            razorpay_client.utility.verify_webhook_signature(
                webhook_body, 
                webhook_signature, 
                webhook_secret
            )
            
            # 2. Parse the JSON payload
            data = json.loads(webhook_body)
            event_type = data.get('event')

            # 3. We only care if the payment was successfully captured
            if event_type == 'payment.captured':
                payment_entity = data['payload']['payment']['entity']
                razorpay_order_id = payment_entity['order_id']
                razorpay_payment_id = payment_entity['id']

                # Find the pending transaction
                try:
                    transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
                    
                    # If the frontend already handled it, just return 200 to tell Razorpay we are good
                    if transaction.status == 'SUCCESS':
                        return Response(status=status.HTTP_200_OK)

                    # Otherwise, the webhook is saving the day! Update the DB.
                    transaction.razorpay_payment_id = razorpay_payment_id
                    transaction.status = 'SUCCESS'
                    transaction.save()

                    # Grant the credits securely
                    user = transaction.user
                    user.subscription_plan = transaction.plan_type
                    
                    if transaction.plan_type == 'BASIC':
                        user.credits += 200
                    elif transaction.plan_type == 'PRO':
                        user.credits += 500
                    user.save()
                    logger.info(f"Webhook successfully processed order {razorpay_order_id} for user {user.username}")

                except Transaction.DoesNotExist:
                    logger.error(f"Webhook error: Transaction for order {razorpay_order_id} not found.")
                    return Response(status=status.HTTP_404_NOT_FOUND)

            return Response(status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            logger.warning("Razorpay Webhook Signature Verification Failed.")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Razorpay Webhook Error: {e}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)