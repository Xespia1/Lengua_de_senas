from djongo import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=100)
    progreso = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre
