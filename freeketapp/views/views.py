import time
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from time import time, localtime, strftime
from freeketapp.models import *
from freeketapp.views.auth_profile_check import get_context


def index(request):
    context = {}
    if request.user.is_authenticated:
        context = get_context(request)
        if context['profile'] == 'org':
            return redirect('organizador')
    else:
        context['islogged'] = 'n'

    eventos = Evento.objects.order_by('-visitas')

    eventos = eventos.filter(fecha__gte=strftime("%Y-%m-%d", localtime(time())), numero_entradas_actual__gte=1)[:3]

    context['eventos'] = eventos
    return render(request, "freeketapp/base.html", context)


@login_required(login_url='/login')
def organizador(request):
    context = get_context(request)
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        return redirect('index')

    return render(request, "freeketapp/organizador.html", context)
