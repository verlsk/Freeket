from django.shortcuts import render

from django.http import HttpResponse
from django.template import loader

from freeketapp.models import *


def index(request):
    template = loader.get_template("freeketapp/index.html")
    return HttpResponse(template.render())


# Create your views here.

def form(request):
    context = {}
    return render(request, "freeketapp/form.html", context)


texts = []


def process_form(request):
    context = {}
    if request.method == 'POST':
        input_text = request.POST['input_text']
        texts.append(input_text)
    context['texts'] = texts
    return render(request, "freeketapp/process_form.html", context)


def crear_evento(request):
    context = {}
    return render(request, "freeketapp/plantilla_eventos.html", context)


def evento_creado(request):
    template = loader.get_template("freeketapp/evento_creado.html")
    context = {}
    if request.method == 'POST':
        titulo = request.POST.get('tituloEvento', '')
        context['titulo'] = titulo
        fecha = request.POST.get('fechaEvento', '')
        fecha = fecha.split("-")
        fecha = fecha[2] + "-" + fecha[1] + "-" + fecha[0]
        hora = request.POST.get('horaEvento', '')
        nentradas = request.POST.get('nEntradas', '')
        nmaxentradas = request.POST.get('nMaxEntradas', '')
        u = Usuario.objects.all()[0] #provisionalmente
        e = Evento(titulo=titulo, fecha=fecha, hora=hora, numero_entradas=nentradas, max_entradas_user=nmaxentradas,
                   organizador=u)
        e.save()


    return render(request, "freeketapp/evento_creado.html", context)
