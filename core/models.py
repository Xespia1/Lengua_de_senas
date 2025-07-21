from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib import admin
from djongo import models
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from django.db import models

class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El usuario debe tener un correo electrónico')
        correo = self.normalize_email(correo)
        usuario = self.model(correo=correo, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(correo, password, **extra_fields)
    
    
class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('admin', 'Administrador'),
    ]
    nombre = models.CharField(max_length=20)
    apellido = models.CharField(max_length=20)
    correo = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    progreso = models.IntegerField(default=0)
    rol = models.CharField(max_length=15, choices=ROL_CHOICES, default='estudiante')
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.nombre

class Leccion(models.Model):
    NIVEL_CHOICES = [
        ('B', 'Básico'),
        ('I', 'Intermedio'),
        ('A', 'Avanzado'),
    ]
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=1, choices=NIVEL_CHOICES)
    video_url = models.URLField(blank=True)
    orden = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_nivel_display()} - {self.titulo}"
    

class Video(models.Model):
    leccion = models.ForeignKey(Leccion, related_name='videos', on_delete=models.CASCADE)
    titulo = models.CharField(default='Nombre', max_length=100)
    url = models.URLField()
    
    def embed_url(self):
        return self.url.replace("watch?v=", "embed/")

    def __str__(self):
        return f"{self.titulo} - {self.leccion.titulo}"

    
class Pregunta(models.Model):
    leccion = models.ForeignKey('Leccion', related_name='preguntas', on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)

    def __str__(self):
        return self.texto

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='respuestas', on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return self.texto

class ResultadoQuiz(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    puntaje = models.IntegerField()
    total = models.IntegerField(default=10)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.leccion} - {self.puntaje}/{self.total}"


class Feedback(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.ForeignKey('Leccion', on_delete=models.CASCADE)
    comentario = models.TextField("Comentario", max_length=500)
    calificacion = models.PositiveSmallIntegerField("Calificación (1 a 5)", choices=[(i, str(i)) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.leccion} ({self.calificacion})"