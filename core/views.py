from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroForm, LoginForm, QuizForm
from .models import Leccion, Pregunta, Respuesta, Usuario
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login

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
            try:
                usuario = Usuario.objects.get(correo=correo)
                if usuario.contraseña == contraseña:
                    request.session['usuario_id'] = usuario.id
                    request.session['usuario_nombre'] = usuario.nombre
                    return redirect('lecciones')
                else:
                    messages.error(request, 'Contraseña incorrecta.')
            except Usuario.DoesNotExist:
                messages.error(request, 'El correo no está registrado.')
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
    nivel = request.GET.get('nivel', 'B')  # B por defecto
    lecciones = Leccion.objects.filter(nivel=nivel).order_by('orden')
    return render(request, 'lecciones.html', {'lecciones': lecciones, 'nivel': nivel})

def logout_view(request):
    request.session.flush()
    return redirect('login')

def quiz_view(request, leccion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    leccion = get_object_or_404(Leccion, pk=leccion_id)
    preguntas = leccion.preguntas.prefetch_related('respuestas')

    if request.method == 'POST':
        form = QuizForm(preguntas, request.POST)
        if form.is_valid():
            puntaje = 0
            total = len(preguntas)
            for pregunta in preguntas:
                respuesta_id = int(form.cleaned_data[f"pregunta_{pregunta.id}"])
                respuesta = Respuesta.objects.get(pk=respuesta_id)
                if respuesta.es_correcta:
                    puntaje += 1
            messages.success(request, f'Resultado: {puntaje}/{total} correctas.')
            return redirect('niveles')
    else:
        form = QuizForm(preguntas)

    return render(request, 'quiz.html', {
        'form': form,
        'leccion': leccion,
    })