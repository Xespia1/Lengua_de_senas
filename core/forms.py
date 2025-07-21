from django import forms
from .models import *
from django.forms import modelformset_factory, BaseModelFormSet

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
            self.fields[f'pregunta_{pregunta.id}'] = forms.ChoiceField(
                label=pregunta.texto,
                choices=opciones,
                widget=forms.RadioSelect,
                required=True,
            )

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['comentario', 'calificacion']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Escribe tu comentario aquí...'}),
            'calificacion': forms.Select(attrs={'class': 'form-select'})
        }

class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['texto']
        widgets = {
            'texto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto de la pregunta'})
        }


class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['texto', 'es_correcta']
        widgets = {
            'texto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternativa'}),
            'es_correcta': forms.RadioSelect,
        }

RespuestaFormSet = modelformset_factory(
    Respuesta,
    form=RespuestaForm,
    extra=0,
    min_num=4,
    validate_min=True
)