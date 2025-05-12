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
]
