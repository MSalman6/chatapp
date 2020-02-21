from django import forms


class CreateContactForm(forms.Form):
	messages = forms.CharField(max_length=2)
	participants = forms.CharField(max_length=200)