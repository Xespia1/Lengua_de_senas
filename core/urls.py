from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('lecciones/', views.seleccionar_nivel, name='lecciones'),
    path('lecciones/<str:nivel>/', views.lecciones_por_nivel, name='lecciones_por_nivel'),
    path('leccion/<int:pk>/', views.ver_leccion, name='ver_leccion'),
    path('quiz/<int:leccion_id>/', views.quiz_view, name='quiz'),
    path('progreso/', views.progreso_usuario, name='progreso_usuario'),
    path('progreso_todos/', views.progreso_estudiantes, name='progreso_estudiantes'),
    path('leccion/<int:leccion_id>/feedback/', views.enviar_feedback, name='enviar_feedback'),
    path('feedback_admin/', views.feedback_admin, name='feedback_admin'),

]
