# queries/forms.py
from django import forms

class SearchForm(forms.Form):
    ic_index = forms.CharField(label='Teilenummer', max_length=100)  # Adjust max_length as needed
