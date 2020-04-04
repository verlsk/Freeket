from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('form', views.form, name = 'form'),
    path('process_form', views.process_form, name ="process_form"),
    path('crear-evento', views.crear_evento, name='crear_evento')
]