from django.contrib import admin
from .models import *

# admin.site.register(Leccion)

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    
class LeccionAdmin(admin.ModelAdmin):
    inlines = [VideoInline]
    
admin.site.register(Leccion, LeccionAdmin)
admin.site.register(Video)
admin.site.register(Pregunta)
admin.site.register(Respuesta)