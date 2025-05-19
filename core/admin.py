from django.contrib import admin
from .models import Leccion, Video

# admin.site.register(Leccion)

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    
class LeccionAdmin(admin.ModelAdmin):
    inlines = [VideoInline]
    
admin.site.register(Leccion, LeccionAdmin)
admin.site.register(Video)