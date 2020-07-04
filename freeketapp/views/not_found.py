from django.shortcuts import render

from freeketapp.views import get_context


def error_404_view(request, exception):
    context = {}
    if request.user.is_authenticated:
        context = get_context(request)
    else:
        context['islogged'] = 'n'

    return render(request, 'freeketapp/404.html', context)