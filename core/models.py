from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from djongo import models

class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=20)
    apellido = models.CharField(max_length=20)
    contraseña = models.CharField(max_length=20)
    correo = models.EmailField(unique=True)
    progreso = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

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
    video_url = models.URLField()
    orden = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_nivel_display()} - {self.titulo}"
    
class Pregunta(models.Model):
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField()

    def __str__(self):
        return f"{self.leccion.titulo}: {self.texto[:30]}..."

class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    texto = models.CharField(max_length=200)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.texto} ({'Correcta' if self.es_correcta else 'Incorrecta'})"

