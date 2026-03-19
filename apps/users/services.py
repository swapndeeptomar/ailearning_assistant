import logging
import uuid
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}

def handle_oauth_user(email, provider, base_username, avatar_url=None):
    """Handles Account Linking, Race Conditions, and Username Collisions."""
    if not email:
        raise ValueError("A verified email is required for authentication.")

    try:
        # Advanced 14: Atomic transaction to prevent race conditions
        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            
            if user:
                # JWT 13: Account Linking Strategy
                if user.provider != provider:
                    logger.info(f"Account Link: {email} logged in via {provider} but originally used {user.provider}")
                    # Optional: Update provider or keep original
                
                # Update avatar if it was previously empty
                if avatar_url and not user.avatar_url:
                    user.avatar_url = avatar_url
                    user.save(update_fields=['avatar_url'])
                    
            else:
                # Data 4: Handle Username Collisions
                username = base_username
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{uuid.uuid4().hex[:6]}"
                
                # Create the new user
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    provider=provider,
                    avatar_url=avatar_url
                )
                
        return user, get_tokens_for_user(user)
        
    except IntegrityError as e:
        logger.error(f"Integrity error during OAuth creation for {email}: {e}")
        raise ValueError("Could not create user account due to a database conflict.")