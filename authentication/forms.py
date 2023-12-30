from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


class ImageUploadForm(forms.Form):
    image = forms.ImageField()

class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

class UserProfileForm(forms.ModelForm):
    username = forms.CharField()  # Add the username field
    email = forms.EmailField()  # Add the email field
    pass1 = forms.CharField(widget=forms.PasswordInput)
    pass2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'pass1', 'pass2', 'profile_picture']


class PhotoUploadForm(forms.Form):
    photo = forms.ImageField()
