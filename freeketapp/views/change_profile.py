from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from freeketapp.models import Organizador


@login_required(login_url='/login')
def perfil_organizador(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}

    orgs = Organizador.objects.filter(id=request.user.id)

    if orgs.count() > 0:
        request.session['profile'] = 'org'
        context['profile'] = request.session['profile']
        return redirect('organizador')
    else:
        # registrar
        pass


@login_required(login_url='/login')
def perfil_asistente(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}

    orgs = Organizador.objects.filter(id=request.user.id)
    request.session['profile'] = 'assist'
    context['profile'] = request.session['profile']
    if orgs.count() == 0:
        return redirect('index')
    else:
        if not orgs[0].exclusive_org:
            return redirect('index')
        else:
            return redirect('registro_asistente')

