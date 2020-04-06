from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('crear-evento', views.crear_evento, name='crear_evento'),
    path('evento-creado', views.evento_creado, name = 'evento_creado'),
    path('evento/<str:id>', views.pagina_evento, name = 'pagina_evento'),
    path('compra-realizada', views.compra_realizada, name='compra_realizada')
]