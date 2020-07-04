from freeketapp.models import Organizador


def get_context(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    return context