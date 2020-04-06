from datetime import datetime

from django.shortcuts import render

from django.http import HttpResponse, Http404
from django.template import loader

from freeketapp.models import *
import locale
import unicodedata

def index(request):
    template = loader.get_template("freeketapp/index.html")
    return HttpResponse(template.render())


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
        url_aux = titulo.replace(" ", "-")
        url_id = ""
        for character in url_aux:
            if character.isalnum() or character == "-":
                url_id += character
        url_id = url_id.lower()
        url_id = str(unicodedata.normalize('NFD', url_id)\
           .encode('ascii', 'ignore')\
           .decode("utf-8"))
        e_number = Evento.objects.filter(url_id=url_id).count()
        if e_number >= 1:
            url_id = url_id + "_" + str(e_number)

        u = Usuario.objects.all()[0]  # provisionalmente
        e = Evento(titulo=titulo, url_id=url_id, fecha=fecha, hora=hora, numero_entradas=nentradas,
                   max_entradas_user=nmaxentradas,
                   organizador=u)
        e.save()

        context['url_id'] = url_id
        context['titulo'] = titulo

    return render(request, "freeketapp/evento_creado.html", context)


def pagina_evento(request, id):
    template = loader.get_template("freeketapp/pagina_evento.html")
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    id = id.lower()

    id = str(unicodedata.normalize('NFD', id) \
                 .encode('ascii', 'ignore') \
                 .decode("utf-8"))

    try:
        evento = Evento.objects.filter(url_id=id)
        if evento.count() == 0:
            urlEvento = id.rsplit("_", 1)
            titEvento = ""
            idEvento = -1
            # la url viene en formato freeket.com/evento/esto-es-un-evento_id
            # con estas lineas procesamos el evento
            if len(urlEvento) > 1:
                idEvento = int(urlEvento[1])
                eventos = Evento.objects.filter(url_id=urlEvento[0])
                if eventos.count() > 1 and 0 <= idEvento < eventos.count():
                    evento = eventos[idEvento]
                else:
                    evento = None
            else:
                evento = None
        else:
            evento = evento[0]

        if evento is None:
            raise Http404("El evento no existe!")
        else:
            context = {}
            titulo_aux = evento.titulo
            context['titulo'] = titulo_aux
            context['nmax'] = evento.max_entradas_user
            eng_date_format = evento.fecha
            esp_date_format = eng_date_format.strftime("%d de %B de %Y")
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
    except Evento.DoesNotExist:
        raise Http404("El evento no existe!")
    except ValueError:
        raise Http404("El evento no existe!")
    return HttpResponse(template.render(context, request))
