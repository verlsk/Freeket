from django.shortcuts import render

from django.http import HttpResponse
from django.template import loader

def index(request):
    template = loader.get_template("freeketapp/index.html")
    return HttpResponse(template.render())
# Create your views here.

def form(request):
    context = {}
    return render (request, "freeketapp/form.html", context)

texts = []

def process_form(request):
    context = {}
    if request.method == 'POST':
        input_text = request.POST['input_text']
        texts.append (input_text)
    context['texts'] = texts
    return render(request, "freeketapp/process_form.html", context)

def crear_evento(request):
    template = loader.get_template("freeketapp/plantilla_eventos.html")
    return HttpResponse(template.render())
