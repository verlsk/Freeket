from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('confirmation/<str:id_confirmacion_url>/<str:user>/', views.confirmation, name="confirmation"),
    path('login/', views.my_login, name="login"),
    path('cerrar-sesion', views.cerrar_sesion, name="cerrar_sesion"),
    path('mi-perfil/reset-password/', views.reset_password, name="reset_password"),
    path('forgot-password/', views.forgot_password_form, name="forgot_password_form"),
    path('crear-evento/', views.crear_evento, name="crear_evento"),
    path('evento/<str:id_evento>/', views.pagina_evento, name = 'pagina_evento'),
    path('mis-entradas/<str:id_entrada>/', views.mostrar_entrada, name='mostrar_entrada'),
    path('mis-entradas/', views.misentradas, name='misentradas'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('mi-perfil/confirmar-email', views.confirmar_email, name='confirmar_email'),
    path('gestionar-eventos/', views.gestionar_eventos, name='gestionar_eventos'),
    path('gestionar-eventos/<str:id_evento>/', views.gestionar_eventos_evento, name='gestionar_eventos_evento'),
    path('gestionar-eventos/<str:id_evento>/modificar/', views.gestionar_eventos_modificar, name='gestionar_eventos_modificar'),
    path('gestionar-eventos/<str:id_evento>/notificacion/', views.gestionar_eventos_notificacion, name='gestionar_eventos_notificacion'),
    path('gestionar-eventos/<str:id_evento>/cancelar-evento/', views.gestionar_eventos_cancelar, name='gestionar_eventos_cancelar'),
    path('gestionar-eventos/<str:id_evento>/asistentes/', views.gestionar_eventos_asistentes,
         name='gestionar_eventos_asistentes'),
    path('eventos/', views.eventos, name='eventos'),
]