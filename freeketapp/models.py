from django.db import models
import uuid
from django.core.files.base import ContentFile

class Usuario(models.Model):
    nickname = models.CharField(max_length=50)
    fecha_registro = models.DateField()
    password = models.CharField(max_length=50)
    email = models.EmailField()
    objects = models.Manager()

class Organizador(models.Model):
    nickname = models.CharField(max_length=50)
    objects = models.Manager
class Evento(models.Model):
    id = models.UUIDField(null=False, primary_key=True, default=uuid.uuid4)
    titulo = models.CharField(max_length=50)
    url_id = models.CharField(max_length=100, default='default')
    fecha = models.DateField()
    hora = models.CharField(max_length=5)
    numero_entradas = models.IntegerField()
    max_entradas_user = models.IntegerField()
    ciudad = models.CharField(max_length=50, default='')
    direccion = models.CharField(max_length=100, default='')
    cpostal = models.CharField(max_length=20, default='')
    key = models.CharField(max_length=100, default='default')
    organizador = models.ForeignKey(Organizador, on_delete=models.CASCADE, default=1)

    objects = models.Manager()

class Entrada(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    id = models.UUIDField(null=False, primary_key=True, default=uuid.uuid4)
    objects = models.Manager()

# Create your models here.