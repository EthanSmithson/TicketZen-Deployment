from django.forms import ModelForm
from django import forms
from .models import User

class UploadForm(ModelForm):
    firstName = forms.TextInput()
    lastName = forms.TextInput()
    username = forms.TextInput()
    password = forms.CharField(widget=forms.PasswordInput())
    repassword = forms.CharField(widget=forms.PasswordInput())
    email = forms.TextInput()
    class Meta:
        model = User
        fields = ['firstName', 'lastName', 'username', 'password', 'repassword', 'email']
    
    def clean(self):
 
        super(UploadForm, self).clean()
         
        password = self.cleaned_data.get('password')
        repassword = self.cleaned_data.get('repassword')
 
        if password != repassword:
            self._errors['password'] = self.error_class([
                'Passwords do not match'])
 
        return self.cleaned_data
    
class LoginForm(ModelForm):
    email = forms.TextInput()
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email', 'password']
    
    def clean(self):

        super(LoginForm, self).clean()
        
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        return self.cleaned_data