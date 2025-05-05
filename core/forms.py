from django import forms
from .models import Usuario

class RegistroForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'contraseña']

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['contraseña'])
        if commit:
            usuario.save()
        return usuario

class LoginForm(forms.Form):
    correo = forms.EmailField()
    contraseña = forms.CharField(widget=forms.PasswordInput)
