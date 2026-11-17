from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from apps.accounts.models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom Social Account Adapter for Google OAuth2.
    
    Enforces strict role-pinning and account linking rules:
    1. Pre-registered Doctor Linking:
       If an administrator pre-created a Doctor account with an email (e.g. dr.sharma@gmail.com),
       and the doctor logs in via Google with that email, link the Google account
       to the existing Doctor profile.
    
    2. Strict Patient Provisioning for New Users:
       If an unknown user signs in via Google for the first time, they are
       strictly provisioned with role = 'PATIENT'. An unregistered user can NEVER
       obtain the DOCTOR or ADMIN role through Google OAuth.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just before a user logs in via social authentication.
        If an account with the verified Google email already exists, link them.
        """
        # If user is already authenticated, let allauth connect normally
        if sociallogin.is_existing:
            return

        email = user_email(sociallogin.user)
        if not email:
            return

        try:
            # Check if user with this email was pre-provisioned (e.g., Doctor created by Admin)
            existing_user = User.objects.get(email__iexact=email)
            # Connect the incoming Google social account to the existing User
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # User is brand new, will proceed to populate_user and save as PATIENT
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Hook called when a new user instance is generated from social account data.
        Guarantees that any brand-new social signup is strictly assigned role='PATIENT'.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract full name from Google profile if available
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        name = data.get('name', '')

        if name:
            user.full_name = name
        elif first_name or last_name:
            user.full_name = f"{first_name} {last_name}".strip()
        else:
            user.full_name = user.email.split('@')[0].capitalize()

        # Enforce role invariant: new signups are strictly PATIENT
        user.role = User.Role.PATIENT
        user.username = user.email
        return user
