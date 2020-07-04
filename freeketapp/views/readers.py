from cryptography.fernet import Fernet
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render

from freeketapp.models import Evento, Entrada
from freeketapp.views import get_context


@login_required(login_url='/login')
def reader(request, id_evento):
    context = get_context(request)
    try:
        ev = Evento.objects.get(url_id=id_evento)
        if ev.organizador.id != request.user.id:
            raise Http404("El evento no existe")
        context['url'] = ev.url_id
    except:
        raise Http404("El evento no existe!")

    return render(request, "freeketapp/reader.html", context)


@login_required(login_url='/login')
def reader_salida(request, id_evento):
    context = get_context(request)

    try:
        ev = Evento.objects.get(url_id=id_evento)
        if ev.organizador.id != request.user.id:
            raise Http404("El evento no existe")
        context['url'] = ev.url_id
    except:
        raise Http404()

    return render(request, "freeketapp/reader-salida.html", context)


def reader_ajax(request):
    if request.is_ajax():

        id_entrada = request.GET.get("id")
        url_id_evento = request.GET.get("url")

        evento = Evento.objects.get(url_id=url_id_evento)

        if evento.organizador.id != request.user.id:
            raise Http404("El evento no existe")

        key = evento.key.encode()
        f = Fernet(key)

        res = {}

        try:

            txt_decoded = f.decrypt(id_entrada.encode()).decode()

            entradas = Entrada.objects.filter(id=txt_decoded, evento=evento)
            if entradas.count() > 0:

                if entradas[0].validada:
                    res['resp'] = 'ya validada'
                else:
                    entrada = entradas[0]
                    entrada.validada = True
                    entrada.save()
                    res['resp'] = True
            else:
                res['resp'] = False
        # no es entrada
        except:
            res['resp'] = False

        return JsonResponse(res)
    else:
        raise Http404("El evento no existe")


def reader_ajax_salida(request):
    if request.is_ajax():

        id_entrada = request.GET.get("id")
        url_id_evento = request.GET.get("url")

        evento = Evento.objects.get(url_id=url_id_evento)

        if evento.organizador.id != request.user.id:
            raise Http404("El evento no existe")

        key = evento.key.encode()
        f = Fernet(key)

        res = {}

        try:
            txt_decoded = f.decrypt(id_entrada.encode()).decode()
            entradas = Entrada.objects.filter(id=txt_decoded, evento=evento)

            if entradas.count() > 0:
                if entradas[0].validada:
                    entrada = entradas[0]
                    entrada.validada = False
                    entrada.save()
                    res['resp'] = True
                else:
                    res['resp'] = "n"
            else:
                res['resp'] = False
        # no es entrada
        except:
            res['resp'] = False

        return JsonResponse(res)
    else:
        raise Http404("El evento no existe")