from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q

def vista_admin(request):
    if request.user.rol != 'admin':
        return redirect('no_autorizado')


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
    if not request.user.is_authenticated or request.user.rol != "estudiante":
        return redirect('login')

    leccion = get_object_or_404(Leccion, pk=leccion_id)
    preguntas = leccion.preguntas.prefetch_related('respuestas')

    if request.method == 'POST':
        form = QuizForm(preguntas, request.POST)
        if form.is_valid():
            puntaje = 0
            total = len(preguntas)
            for pregunta in preguntas:
                respuesta_id = int(form.cleaned_data.get(f"pregunta_{pregunta.id}", 0))
                if respuesta_id:
                    respuesta = Respuesta.objects.get(pk=respuesta_id)
                    if respuesta.es_correcta:
                        puntaje += 1
            usuario = request.user
            ResultadoQuiz.objects.create(
                usuario=usuario,
                leccion=leccion,
                puntaje=puntaje,
                total=total
            )
            messages.success(request, f'¡Tu puntaje es: {puntaje}/{total}!')
            return redirect('lecciones')

    else:
        form = QuizForm(preguntas)

    return render(request, 'quiz.html', {
        'form': form,
        'leccion': leccion,
    })
#Estudiantes
@login_required
def progreso_usuario(request):
    usuario = request.user
    total_lecciones = Leccion.objects.count()
    lecciones_completadas = ResultadoQuiz.objects.filter(
        usuario=usuario, puntaje__gte=1
    ).values_list('leccion_id', flat=True)
    completadas = len(set(lecciones_completadas))
    porcentaje = int((completadas / total_lecciones) * 100) if total_lecciones > 0 else 0

    resultados = ResultadoQuiz.objects.filter(usuario=usuario).select_related('leccion').order_by('-fecha')

    return render(request, 'lecciones/progreso.html', {
        'resultados': resultados,
        'porcentaje': porcentaje,
    })
    
#Docentes
@login_required
def progreso_estudiantes(request):
    if not request.user.is_authenticated or request.user.rol != "docente":
        return redirect('lecciones')

    resultados = ResultadoQuiz.objects.select_related('usuario', 'leccion').all().order_by('-fecha')

    context = {
        'resultados': resultados,
    }
    return render(request, 'lecciones/progreso_todos.html', context)

def progreso_todos(request):
    resultados = ResultadoQuiz.objects.select_related('usuario', 'leccion').all().order_by('-fecha')

    # Cálculo del progreso general (ejemplo: porcentaje de quizzes aprobados por todos los estudiantes)
    total_lecciones = Leccion.objects.count()
    total_usuarios = Usuario.objects.count()

    # Si quieres porcentaje de quizzes completados (independiente del puntaje):
    total_resultados = ResultadoQuiz.objects.count()
    total_posibles = total_lecciones * total_usuarios
    porcentaje = int((total_resultados / total_posibles) * 100) if total_posibles > 0 else 0

    # Quizzes aprobados
    # quizzes_aprobados = ResultadoQuiz.objects.filter(puntaje=F('total')).count()
    # porcentaje = int((quizzes_aprobados / total_posibles) * 100) if total_posibles > 0 else 0

    return render(request, 'lecciones/progreso_todos.html', {
        'resultados': resultados,
        'porcentaje': porcentaje,
    })