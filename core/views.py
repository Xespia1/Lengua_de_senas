from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from collections import defaultdict
from django.forms import modelformset_factory
from django.utils import timezone
from datetime import timedelta


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
    BLOQUEO_MINUTOS = 1
    MAX_INTENTOS = 3
    
    ahora = timezone.localtime()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            contraseña = form.cleaned_data['contraseña']

            try:
                usuario = Usuario.objects.get(correo=correo)
            except Usuario.DoesNotExist:
                usuario = None

            if usuario:
                if usuario.bloqueado_hasta and ahora < usuario.bloqueado_hasta:
                    messages.error(
                        request,
                        f"Has superado el máximo de intentos. Intenta nuevamente a las {usuario.bloqueado_hasta.strftime('%H:%M:%S')}."
                    )
                    return render(request, 'login.html', {'form': form})

                user_auth = authenticate(request, username=correo, password=contraseña)
                if user_auth is not None:
                    auth_login(request, user_auth)
                    usuario.intentos_fallidos = 0
                    usuario.bloqueado_hasta = None
                    usuario.save()
                    return redirect('lecciones')
                else:
                    usuario.intentos_fallidos += 1
                    if usuario.intentos_fallidos >= MAX_INTENTOS:
                        usuario.bloqueado_hasta = ahora + timedelta(minutes=BLOQUEO_MINUTOS)
                        messages.error(request, f"Has superado el máximo de intentos. Intenta nuevamente a las {usuario.bloqueado_hasta.strftime('%H:%M:%S')}.")
                    else:
                        restantes = MAX_INTENTOS - usuario.intentos_fallidos
                        messages.error(request, f"Correo o contraseña incorrectos. Intentos restantes: {restantes}")
                    usuario.save()
            else:
                messages.error(request, "Correo o contraseña incorrectos.")

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

@login_required
def lecciones_por_nivel(request, nivel):
    lecciones = Leccion.objects.filter(nivel=nivel).order_by('orden')
    NIVEL_CHOICES = {
        'B': 'Básico',
        'I': 'Intermedio',
        'A': 'Avanzado'
    }
    nombre_nivel = NIVEL_CHOICES.get(nivel, 'Desconocido')
    
    for leccion in lecciones:
        leccion.nombre_nivel = NIVEL_CHOICES.get(leccion.nivel, 'Desconocido')
        
    return render(request, 'lecciones/listado.html', {
        'lecciones': lecciones,
        'nivel': nombre_nivel
    })

@login_required
def ver_leccion(request, pk):
    leccion = get_object_or_404(Leccion, pk=pk)
    form = FeedbackForm()
    return render(request, 'lecciones/ver_leccion.html', {'leccion': leccion, 'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('login')

@login_required
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
    if not request.user.is_authenticated or request.user.rol in {'docente, admin'}:
        messages.error(request,'No tienes los permisos necesarios para acceder a esta página')
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

@login_required
def editar_quiz(request, leccion_id):
    leccion = get_object_or_404(Leccion, pk=leccion_id)
    preguntas = Pregunta.objects.filter(leccion=leccion).prefetch_related('respuestas')
    mensaje_error = None

    pregunta_editar = None
    editar_form = None
    editar_formset = None

    if request.method == "POST":
        if 'eliminar_pregunta' in request.POST:
            pregunta = get_object_or_404(Pregunta, pk=request.POST.get('pregunta_id'))
            pregunta.delete()
            messages.success(request, "Pregunta eliminada.")
            return redirect('editar_quiz', leccion_id=leccion_id)
        # Inline
        elif 'editar_pregunta' in request.POST:
            pregunta_editar = get_object_or_404(Pregunta, pk=request.POST.get('pregunta_id'))
            editar_form = PreguntaForm(instance=pregunta_editar)
            RespuestaFormSet = modelformset_factory(Respuesta, form=RespuestaForm, extra=0, min_num=2, validate_min=True)
            editar_formset = RespuestaFormSet(queryset=pregunta_editar.respuestas.all())
        
        elif 'guardar_editar' in request.POST:
            pregunta_editar = get_object_or_404(Pregunta, pk=request.POST.get('pregunta_id'))
            editar_form = PreguntaForm(request.POST, instance=pregunta_editar)
            RespuestaFormSet = modelformset_factory(Respuesta, form=RespuestaForm, extra=0, min_num=2, validate_min=True)
            editar_formset = RespuestaFormSet(request.POST, queryset=pregunta_editar.respuestas.all())
            correcta_idx = request.POST.get('editar_correcta')
            if editar_form.is_valid() and editar_formset.is_valid():
                if correcta_idx is None:
                    mensaje_error = "Debes marcar una alternativa como correcta."
                else:
                    editar_form.save()
                    for idx, form in enumerate(editar_formset.forms):
                        respuesta = form.save(commit=False)
                        respuesta.pregunta = pregunta_editar
                        respuesta.es_correcta = (str(idx) == correcta_idx)
                        respuesta.save()
                    messages.success(request, "Pregunta actualizada correctamente.")
                    return redirect('editar_quiz', leccion_id=leccion_id)

        else:
            pregunta_form = PreguntaForm(request.POST)
            alternativas = [request.POST.get(f"nueva_alternativa_{i}") for i in range(4)]
            correcta = request.POST.get("nueva_correcta")
            if pregunta_form.is_valid() and all(alternativas) and correcta is not None:
                pregunta = pregunta_form.save(commit=False)
                pregunta.leccion = leccion
                pregunta.save()
                for idx, texto in enumerate(alternativas):
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        texto=texto,
                        es_correcta=(str(idx) == correcta)
                    )
                messages.success(request, "Pregunta agregada.")
                return redirect('editar_quiz', leccion_id=leccion_id)
            else:
                mensaje_error = "Completa todos los campos y selecciona la respuesta correcta."
    else:
        pregunta_form = PreguntaForm()

    context = {
        'leccion': leccion,
        'preguntas': preguntas,
        'pregunta_form': PreguntaForm(),
        'mensaje_error': mensaje_error,
        'pregunta_editar': pregunta_editar,
        'editar_form': editar_form,
        'editar_formset': editar_formset,
    }
    return render(request, 'lecciones/editar_quiz.html', context)


@login_required
def editar_pregunta(request, leccion_id, pregunta_id):
    pregunta = get_object_or_404(Pregunta, pk=pregunta_id, leccion_id=leccion_id)
    respuestas = list(Respuesta.objects.filter(pregunta=pregunta).order_by('id'))

    if request.method == 'POST':
        pregunta_form = PreguntaForm(request.POST, instance=pregunta)
        textos = [
            request.POST.get(f"alternativa_{i}", "").strip() for i in range(len(respuestas))
        ]
        correcta = request.POST.get("correcta")

        # Validar campos
        if not pregunta_form.is_valid() or not all(textos) or correcta is None:
            messages.error(request, "Debes completar todos los campos y marcar la alternativa correcta.")
        else:
            pregunta_form.save()
            for idx, respuesta in enumerate(respuestas):
                respuesta.texto = textos[idx]
                respuesta.es_correcta = (str(idx) == correcta)
                respuesta.save()
            messages.success(request, "Pregunta y alternativas editadas correctamente.")
            return redirect('editar_quiz', leccion_id=leccion_id)
    else:
        pregunta_form = PreguntaForm(instance=pregunta)

    alternativas = respuestas

    return render(request, "lecciones/editar_pregunta.html", {
        'pregunta_form': pregunta_form,
        'pregunta': pregunta,
        'leccion': pregunta.leccion,
        'alternativas': alternativas,
    })

