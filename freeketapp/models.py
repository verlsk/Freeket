from django.db import models
import uuid
from django.conf import settings
from datetime import date


class Organizador(models.Model):
    nickname = models.CharField(max_length=50)
    exclusive_org = models.BooleanField(default=True)
    direccion = models.CharField(max_length=100, default='')
    objects = models.Manager


class Evento(models.Model):
    id = models.UUIDField(null=False, primary_key=True, default=uuid.uuid4)
    titulo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=20000, default="")
    url_id = models.CharField(max_length=100, default='default')
    fecha = models.DateField()
    hora = models.CharField(max_length=5)
    numero_entradas_inicial = models.IntegerField(default=1)
    numero_entradas_actual = models.IntegerField(default=1)
    max_entradas_user = models.IntegerField()
    ciudad = models.CharField(max_length=50, default='')
    direccion = models.CharField(max_length=100, default='')
    cpostal = models.CharField(max_length=20, default='')
    key = models.CharField(max_length=100, default='default')
    organizador = models.ForeignKey(Organizador, on_delete=models.CASCADE, default=1)
    fecha_creacion = models.DateField(default=date.today())
    visitas = models.IntegerField(default=0)
    img = models.ImageField(upload_to='m', blank=True)

    objects = models.Manager()


class Entrada(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    id = models.UUIDField(null=False, primary_key=True, default=uuid.uuid4)
    fecha_adquisicion = models.DateField(default=date.today())
    objects = models.Manager()


class ConfirmationCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    objects = models.Manager()
# Create your models here.
