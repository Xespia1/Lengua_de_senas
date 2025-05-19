from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroForm, LoginForm, QuizForm
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            contraseña = form.cleaned_data['contraseña']

            usuario = authenticate(request, username=correo, password=contraseña)

            if usuario is not None:
                auth_login(request, usuario)
                return redirect('lecciones')
            else:
                messages.error(request, 'Correo o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def home(request):
    return render(request, 'home.html')

def seleccionar_nivel(request):
    return render(request, 'lecciones/niveles.html')

def lecciones_por_nivel(request, nivel):
    lecciones = Leccion.objects.filter(nivel=nivel).order_by('orden')
    NIVEL_CHOICES = {
        'B': 'Básico',
        'I': 'Intermedio',
        'A': 'Avanzado'
    }
    nombre_nivel = NIVEL_CHOICES.get(nivel, 'Desconocido')
    return render(request, 'lecciones/listado.html', {
        'lecciones': lecciones,
        'nivel': nombre_nivel
    })

def ver_leccion(request, pk):
    leccion = get_object_or_404(Leccion, pk=pk)
    return render(request, 'lecciones/ver_leccion.html', {'leccion': leccion})


def logout_view(request):
    request.session.flush()
    return redirect('login')

def quiz_view(request, leccion_id):
    if not request.user.is_authenticated:
        return redirect('login')

    leccion = Leccion.objects.get(pk=leccion_id)
    preguntas = leccion.preguntas.prefetch_related('respuestas')
    if request.method == 'POST':
        form = QuizForm(preguntas, request.POST)
        if form.is_valid():
            pass
    else:
        form = QuizForm(preguntas)
    return render(request, 'quiz.html', {'form': form, 'leccion': leccion})