from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('registro-realizado/', views.registro_realizado, name="registro-realizado"),
    path('confirmation/<str:id>/<str:user>/', views.confirmation, name="confirmation"),
    path('login/', views.my_login, name="login"),
    path('mi-perfil/reset-password/', views.reset_password, name="reset_password"),
    path('forgot-password/', views.forgot_password_form, name="forgot_password_form"),
    path('crear-evento/', views.crear_evento, name='crear_evento'),
    path('evento-creado/', views.evento_creado, name = 'evento_creado'),
    path('evento/<str:id>/', views.pagina_evento, name = 'pagina_evento'),
    path('compra-realizada/', views.compra_realizada, name='compra_realizada'),
    path('mis-entradas/<str:id>/', views.mostrar_entrada, name='mostrar_entrada'),
    path('mis-entradas/', views.misentradas, name='misentradas')
]