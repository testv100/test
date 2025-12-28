from django import forms

class ResultsUploadForm(forms.Form):
    file = forms.FileField()
    preview = forms.BooleanField(required=False, initial=True)

class TeacherUserLinkForm(forms.Form):
    user_id = forms.IntegerField()
    teacher_id = forms.IntegerField()
