from django.contrib.auth.backends import ModelBackend
from django.urls import reverse

class CustomAuthBackend(ModelBackend):
    def get_user_redirect_url(self, user):
        if user.is_staff:
            return reverse('dashboard_admin')  # Redirect admin user to dashboard_admin
        else:
            return reverse('dashboard')  # Redirect regular user to dashboard

    def get_user(self, user_id):
        return super().get_user(user_id)

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Authenticate the user as you normally would
        user = super().authenticate(request, username, password, **kwargs)

        if user:
            request.session['next_redirect_url'] = self.get_user_redirect_url(user)

        return user
