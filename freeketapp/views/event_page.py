import locale
import threading
import unicodedata
import uuid
from datetime import date

from django.http import Http404
from django.shortcuts import render

from freeketapp.models import Evento, ConfirmationCode, Entrada, ListaEspera
from freeketapp.views import get_context, enviar_entrada


def pagina_evento(request, id_evento):
    context = {}
    if request.user.is_authenticated:
        context = get_context(request)
    else:
        context['islogged'] = 'n'
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    id_evento = id_evento.lower()
    errores = []
    id_evento = str(unicodedata.normalize('NFD', id_evento)
                    .encode('ascii', 'ignore')
                    .decode("utf-8"))

    try:
        evento = Evento.objects.get(url_id=id_evento)
        if request.method == 'POST':

            id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)
            nentradas = int(request.POST.get('nComprarEntradas', '1'))
            id_evento = request.POST.get('idEvento', '')

            e = evento
            entradas_evento_usuario = Entrada.objects.filter(usuario=request.user, evento=e).count()
            if request.user.id == evento.organizador.id or context['profile'] == 'org':
                errores.append("Como organizador del evento, no puedes adquirir entradas")
            if id_confirmacion.count() > 0:
                errores.append("Necesitas confirmar el email antes de adquirir una entrada")
            if nentradas > e.numero_entradas_actual and entradas_evento_usuario + nentradas <= e.max_entradas_user != 0:
                strerror = "No hay tantas entradas disponibles. Lo máximo que puedes adquirir es " + str(
                    e.numero_entradas_actual)
                errores.append(strerror)

            if entradas_evento_usuario == e.max_entradas_user and e.max_entradas_user != 0:
                errores.append("Ya has adquirido el máximo de entradas para este evento")
            elif entradas_evento_usuario + nentradas > e.max_entradas_user != 0:
                strerror = "No puedes adquirir tantas entradas. El máximo de entradas que te quedan por adquirir es " + str(
                    e.max_entradas_user - entradas_evento_usuario)
                errores.append(strerror)

            # controlamos que el máximo de entradas por usuario no sobrepase el número total de entradas que quedan

            if len(errores) == 0:
                # uuid para cada nueva entrada
                for i in range(nentradas):
                    id_entrada = uuid.uuid4()
                    entrada = Entrada(usuario=request.user, evento=e, id=id_entrada)
                    entrada.save()
                    t = threading.Thread(target=enviar_entrada, args=(entrada,), kwargs={})
                    t.setDaemon(True)
                    t.start()
                # actualizacion del numero de entradas
                e.numero_entradas_actual -= nentradas
                e.save()
                context['adquiridas'] = 'y'
            context['errores'] = errores
        if evento is None:
            raise Http404("El evento no existe!")
        else:
            if request.method == 'GET':
                evento.visitas += 1
                evento.save()

            titulo_aux = evento.titulo
            context['titulo'] = titulo_aux
            context['img'] = evento.img.url
            if evento.max_entradas_user != 0:
                context['nmax'] = evento.max_entradas_user
            else:
                context['nmax'] = 15
            eng_date_format = evento.fecha
            if eng_date_format < date.today():
                context['mostrarcomprar'] = 'n'
            else:
                context['mostrarcomprar'] = 'y'

            if evento.numero_entradas_actual == 0:
                context['mostrarcomprar'] = 'n'

                if context['islogged'] == 'y':
                    context['listaespera'] = 'y'
                    l_espera = ListaEspera.objects.filter(evento=evento, usuario=request.user)

                    if l_espera.count() > 0:
                        context['listaespera'] = 'disabled'

            esp_date_format = eng_date_format.strftime("%A %d de %B de %Y")
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = id_evento
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
            context['descripcion'] = evento.descripcion

    except Evento.DoesNotExist:
        raise Http404("El evento no existe!")
    except ValueError:
        raise Http404("El evento no existe!")

    return render(request, "freeketapp/pagina_evento.html", context)