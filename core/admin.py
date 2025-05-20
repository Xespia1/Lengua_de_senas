from django.contrib import admin
from .models import *

# admin.site.register(Leccion)

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    
class LeccionAdmin(admin.ModelAdmin):
    inlines = [VideoInline]
    
class ResultadoQuizAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'leccion', 'puntaje', 'total', 'fecha')
    list_filter = ('usuario', 'leccion')

    
admin.site.register(Leccion, LeccionAdmin)
admin.site.register(Video)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(Usuario)
admin.site.register(ResultadoQuiz,ResultadoQuizAdmin)