from django import forms

class ResultsUploadForm(forms.Form):
    file = forms.FileField()
    preview = forms.BooleanField(required=False, initial=True)

class TeacherUserLinkForm(forms.Form):
    user_id = forms.IntegerField()
    teacher_id = forms.IntegerField()
from django import forms
from .models import News
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["title", "body", "is_published", "source", "source_url"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "source": forms.TextInput(attrs={"class": "form-control"}),
            "source_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }
