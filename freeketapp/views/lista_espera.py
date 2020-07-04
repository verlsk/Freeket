from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from freeketapp.models import ListaEspera, Evento
from freeketapp.views import get_context


@login_required(login_url='/login')
def lista_espera(request):
    context = get_context(request)

    if request.method == 'POST':
        url_id = request.POST.get('idEventoLista')
        try:

            evento = Evento.objects.get(url_id=url_id)
            l_espera = ListaEspera(usuario=request.user, evento=evento)
            l_espera.save()
            esp_date_format = evento.fecha.strftime("%A %d de %B de %Y")
            context['titulo'] = evento.titulo
            context['img'] = evento.img.url
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = url_id
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
            context['descripcion'] = evento.descripcion
            context['listaespera'] = 'anadido'
            return render(request, "freeketapp/pagina_evento.html", context)

        except:
            raise Http404()
    else:
        return redirect('eventos')


@login_required(login_url='/login')
def quitar_lista_espera(request):
    context = get_context(request)

    if request.method == 'POST':
        url_id = request.POST.get('idEventoLista')
        try:

            evento = Evento.objects.get(url_id=url_id)

            l_espera = ListaEspera.objects.get(usuario=request.user, evento=evento)
            l_espera.delete()

            esp_date_format = evento.fecha.strftime("%A %d de %B de %Y")
            context['titulo'] = evento.titulo
            context['img'] = evento.img.url
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = url_id
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
            context['descripcion'] = evento.descripcion
            context['listaespera'] = 'quitado'
            return render(request, "freeketapp/pagina_evento.html", context)

        except:
            raise Http404()
    else:
        return redirect('eventos')