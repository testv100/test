from django import forms


class ResultsUploadForm(forms.Form):
    file = forms.FileField(label='Файл с результатами (CSV)')
