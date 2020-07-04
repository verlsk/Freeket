from time import strftime, localtime, time

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render

from freeketapp.models import Evento
from freeketapp.views import get_context


def eventos(request):
    context = {}
    if request.user.is_authenticated:
        context = get_context(request)

    else:
        context['islogged'] = 'n'

    evs = Evento.objects.all()

    titulo = request.GET.get("titulo")

    if titulo is not None:
        evs = Evento.objects.filter(titulo__icontains=titulo,
                                    fecha__gte=strftime("%Y-%m-%d", localtime(time()))).order_by('-visitas')[:7]
    context['evs'] = evs

    if request.is_ajax():
        for i in range(len(evs)):
            evs[i].key = ""
            evs[i].organizador.id = ""
            evs[i].visitas = ""
            evs[i].numero_entradas_inicial = ""
            evs[i].numero_entradas_actual = ""
            evs[i].id = ""

        data = serializers.serialize('json', evs)

        return HttpResponse(data, content_type="application/json")
    else:
        eventos = Evento.objects.order_by('-visitas')
        eventos = eventos.filter(fecha__gte=strftime("%Y-%m-%d", localtime(time())))
        context['mode'] = 'pop'
        if request.method == 'POST':
            ordenado = request.POST.get('ordenado')
            if ordenado == '0':
                eventos = eventos.order_by('-fecha_creacion')

                print(eventos)

                context['mode'] = 'fecha'
        n = 3
        eventos_total = [eventos[i * n:(i + 1) * n] for i in range((len(eventos) + n - 1) // n)]
        context['eventos_total'] = eventos_total

        if len(eventos) == 0:
            context['eventos_total'] = None

    return render(request, "freeketapp/eventos.html", context)


def resultados(request):
    context = {}
    if request.user.is_authenticated:
        context = get_context(request)
    else:
        context['islogged'] = 'n'

    if request.method == 'POST':
        nombre = request.POST.get('titulo')
        evs = Evento.objects.filter(titulo__icontains=nombre)
        evs = evs.filter(fecha__gte=strftime("%Y-%m-%d", localtime(time())))
        n = 3
        evs_total = [evs[i * n:(i + 1) * n] for i in range((len(evs) + n - 1) // n)]
        context['eventos_total'] = evs_total

        if len(evs) == 0:
            context['eventos_total'] = None
    return render(request, "freeketapp/resultados.html", context)