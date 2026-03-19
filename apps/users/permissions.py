from rest_framework.permissions import BasePermission

class HasSufficientCredits(BasePermission):
    """
    Allows access only to users who have a positive credit balance.
    """
    message = "Insufficient credits. Please upgrade your plan to continue using AI features."

    def has_permission(self, request, view):
        # Allow if the user is authenticated and has more than 0 credits
        return bool(request.user and request.user.is_authenticated and request.user.credits > 0)