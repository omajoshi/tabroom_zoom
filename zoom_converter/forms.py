from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, School

class TournamentAccessForm(forms.Form):
    email = forms.EmailField()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'tabroom_email', 'zoom_email', 'first_name', 'last_name']

class SchoolContactEmailForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['contact_email']

class EmailActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'email_confirmed']
        widgets = {
            'email_confirmed': forms.CheckboxInput(attrs={'disabled': True}),
        }


class TabroomActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['tabroom_email', 'tabroom_confirmed']
        widgets = {
            'tabroom_confirmed': forms.CheckboxInput(attrs={'disabled': True}),
        }

class ZoomActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['zoom_email', 'zoom_confirmed']
        widgets = {
            'zoom_confirmed': forms.CheckboxInput(attrs={'disabled': True}),
        }

