from django.shortcuts import render, redirect
from .forms import RegistroForm, LoginForm
from .models import Usuario, Leccion
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
    leccion = Leccion.objects.get(pk=pk)
    return render(request, 'lecciones/ver.html', {'leccion': leccion})

def logout_view(request):
    request.session.flush()
    return redirect('login')
