from django import forms
from .models import Usuario
from .models import Pregunta, Respuesta

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
    correo = forms.EmailField(label="Correo electrónico",
            widget=forms.EmailInput(attrs={
                'placeholder': 'ejemplo@correo.com',
                'class': 'form-control',
            }))
    contraseña = forms.CharField(widget=forms.PasswordInput(attrs={
            'placeholder': '********',
            'class': 'form-control',
        }))
    
class QuizForm(forms.Form):
    def __init__(self, preguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for pregunta in preguntas:
            opciones = [(r.id, r.texto) for r in pregunta.respuestas.all()]
            self.fields[f"pregunta_{pregunta.id}"] = forms.ChoiceField(
                label=pregunta.texto,
                choices=opciones,
                widget=forms.RadioSelect
            )
