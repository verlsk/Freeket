from django.db import models
from freeket import settings

class Usuario(models.Model):
    nickname = models.CharField(max_length=50)
    fecha_registro = models.DateField()
    password = models.CharField(max_length=50)
    email = models.EmailField()
    objects = models.Manager()

class Evento(models.Model):
    titulo = models.CharField(max_length=50)
    fecha = models.DateField()
    hora = models.CharField(max_length=5)
    numero_entradas = models.IntegerField()
    max_entradas_user = models.IntegerField()
    organizador = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    objects = models.Manager()


# Create your models here.
