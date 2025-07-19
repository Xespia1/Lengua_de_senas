from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from collections import defaultdict

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

@login_required
def seleccionar_nivel(request):
    usuario = request.user

    # *** Básico ***
    basico = Leccion.objects.filter(nivel='B')
    basico_ids = list(basico.values_list('id', flat=True))
    basico_resultados = ResultadoQuiz.objects.filter(
        usuario=usuario, leccion__in=basico_ids, puntaje__gte=1
    ).values_list('leccion', flat=True)
    basico_completadas = len(set(basico_resultados))
    total_basico = basico.count()
    basico_completado = basico_completadas == total_basico and total_basico > 0

    # *** Intermedio ***
    intermedio = Leccion.objects.filter(nivel='I')
    intermedio_ids = list(intermedio.values_list('id', flat=True))
    intermedio_resultados = ResultadoQuiz.objects.filter(
        usuario=usuario, leccion__in=intermedio_ids, puntaje__gte=1
    ).values_list('leccion', flat=True)
    intermedio_completadas = len(set(intermedio_resultados))
    total_intermedio = intermedio.count()
    intermedio_completado = intermedio_completadas == total_intermedio and total_intermedio > 0

    return render(request, 'lecciones/niveles.html', {
        'basico_completado': basico_completado,
        'intermedio_completado': intermedio_completado,
    })

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
    form = FeedbackForm()
    return render(request, 'lecciones/ver_leccion.html', {'leccion': leccion, 'form': form})


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
    resultados_usuario = ResultadoQuiz.objects.filter(usuario=usuario)
    lecciones_completadas = set()
    for resultado in resultados_usuario:
        if resultado.total > 0 and resultado.puntaje >= (resultado.total * 0.6):
            lecciones_completadas.add(resultado.leccion_id)
    completadas = len(set(lecciones_completadas))
    porcentaje = int((completadas / total_lecciones) * 100) if total_lecciones > 0 else 0

    resultados = ResultadoQuiz.objects.filter(usuario=usuario).select_related('leccion').order_by('-fecha')
    for resultado in resultados:
        resultado.aprobado = resultado.total > 0 and resultado.puntaje >= (resultado.total * 0.6)

    return render(request, 'lecciones/progreso.html', {
        'resultados': resultados,
        'porcentaje': porcentaje,
    })
    
#Docentes
@login_required
def progreso_estudiantes(request):
    if not request.user.is_authenticated or request.user.rol != "docente":
        return redirect('lecciones')

    resultados = ResultadoQuiz.objects.select_related('usuario', 'leccion').order_by('usuario', 'leccion', '-fecha')
    ultimos_resultados = {}
    historial_listo = []
    for resultado in resultados:
        resultado.aprobado = resultado.total > 0 and resultado.puntaje >= (resultado.total * 0.6)


    agrupados = defaultdict(list)
    for res in resultados:
        res.aprobado = res.total > 0 and res.puntaje >= (res.total * 0.6)
        res.porcentaje = int((res.puntaje / res.total) * 100) if res.total > 0 else 0
        key = (res.usuario.id, res.leccion.id)
        agrupados[key].append(res)
        
    for key, intentos in agrupados.items():
        mas_reciente = intentos[0]
        historial = intentos[1:]
        for intento in historial:
            intento.porcentaje = int((intento.puntaje / intento.total) * 100) if intento.total > 0 else 0
        mas_reciente.historial = historial
        ultimos_resultados[key] = mas_reciente
        historial_listo.append(mas_reciente)

    context = {
        'ultimos_resultados': historial_listo,
    }
    return render(request, 'lecciones/progreso_todos.html', context)


@login_required
def enviar_feedback(request, leccion_id, ):
    leccion = get_object_or_404(Leccion, pk=leccion_id)
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.usuario = request.user
            feedback.leccion = leccion
            feedback.save()
            messages.success(request, "¡Gracias por tu feedback!")
            return redirect('lecciones')
    else:
        form = FeedbackForm()
    return render(request, "lecciones/feedback_modal.html", {"form": form, "leccion": leccion})
    

@login_required
def feedback_admin(request):
    if request.user.rol not in ["admin", "docente"]:
        return redirect('lecciones')
    feedbacks = Feedback.objects.select_related('usuario', 'leccion').order_by('-fecha')
    return render(request, "lecciones/feedback_admin.html", {"feedbacks": feedbacks})