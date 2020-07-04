import os
import unicodedata
import uuid
from datetime import datetime, date

from cryptography.fernet import Fernet
from django.shortcuts import redirect, render
from freeketapp.models import Organizador, Evento
from freeketapp.views import get_context
from django.contrib.auth.decorators import login_required

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def validate_date(date_text):
    try:
        fecha = date_text.split("-")
        fecha = fecha[2] + "-" + fecha[1] + "-" + fecha[0]
        if datetime.strptime(fecha, '%Y-%m-%d').date() <= date.today():
            return False
        return fecha
    except ValueError:
        return False
    except IndexError:
        return False


def isTimeFormat(input):
    try:
        datetime.strptime(input, '%H:%M')
        if len(input.split(":")[0]) > 2 or len(input.split(":")[1]) != 2:
            return False
        else:
            return True
    except ValueError:
        return False


@login_required(login_url='/login')
def crear_evento(request):
    context = get_context(request)
    errores = []
    if request.method == 'POST':
        # try:
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            return redirect('registro_organizador')
        else:
            if request.session['profile'] == 'org':
                org = org[0]
        titulo = request.POST.get('tituloEvento', '')
        context['titulo'] = titulo

        img = ''
        allow_big_size = False
        try:
            img = request.FILES['imgEvento']
        except:
            img = 'm/default.jpg'
            allow_big_size = True
        descripcion = request.POST.get('descripcion', '')
        if descripcion == '':
            context['b_det'] = 'border-danger'
            errores.append("Escribe una descripción acerca de tu evento")
        elif len(descripcion) > 20000:
            context['b_det'] = 'border-danger'
            errores.append("Tu descripción es demasiado larga")
        # formatear la fecha para que la bbdd la pueda almacenar
        fecha = request.POST.get('fechaEvento', '')
        fecha = validate_date(fecha)
        if not fecha:
            context['b_f'] = 'border-danger'
            errores.append("Formato de fecha incorrecto")

        hora = request.POST.get('horaEvento', '')

        if not isTimeFormat(hora):
            context['b_h'] = 'border-danger'
            errores.append("Formato de hora incorrecto")

        nentradas = request.POST.get('nEntradas', '')
        nmaxentradas = request.POST.get('nMaxEntradas', '')
        ciudad = request.POST.get('ciudad', '')
        cpostal = request.POST.get('cpostal', '')
        direccion = request.POST.get('direccion', '')
        url_aux = titulo.replace(" ", "-")
        url_id = ""
        # eliminar caracteres especiales de la url
        for character in url_aux:
            if character.isalnum() or character == "-":
                url_id += character
        url_id = url_id.lower()
        # eliminar acentos de la url
        url_id = str(unicodedata.normalize('NFD', url_id)
                     .encode('ascii', 'ignore')
                     .decode("utf-8"))
        # consultar si ya existe un evento con esa url
        e_number = Evento.objects.filter(url_id=url_id).count()
        # si existe, se añade una distinción a la url
        if e_number >= 1:
            url_id = url_id + "_" + str(e_number)
        context['url_id'] = url_id

        if titulo == '':
            context['b_t'] = 'border-danger'
            errores.append("El título no puede estar vacío")
        if nentradas == '':
            context['b_n'] = 'border-danger'
            errores.append("Tienes que especificar un número de entradas")
        if ciudad == '':
            context['b_ciu'] = 'border-danger'
            errores.append("La ciudad no puede estar vacía")
        if direccion == '':
            context['b_dir'] = 'border-danger'
            errores.append("La dirección no puede estar vacía")
        if cpostal == '':
            context['b_cp'] = 'border-danger'
            errores.append("El código postal no puede estar vacío")
        if not RepresentsInt(nentradas) or int(nentradas) < 0:
            context['b_n'] = 'border-danger'
            errores.append("Número de entradas no válido")
        if int(nmaxentradas) < 0 or int(nmaxentradas) > 10:
            context['b_nmax'] = 'border-danger'
            errores.append("El número máximo de entradas por usuario no es válido")

        if len(errores) == 0:
            context['publicado'] = True
            context['errores'] = None

            # generamos clave para desencriptar entradas de evento
            key = Fernet.generate_key().decode()
            # uuid para evento
            id_evento = uuid.uuid4()
            # usuario que organiza el evento
            e = Evento(id=id_evento, img=img, descripcion=descripcion, titulo=titulo, url_id=url_id, fecha=fecha,
                       hora=hora,
                       numero_entradas_inicial=nentradas,
                       max_entradas_user=nmaxentradas, numero_entradas_actual=nentradas,
                       organizador=org, key=key, ciudad=ciudad, direccion=direccion, cpostal=cpostal)

            if e.img.width < e.img.height:
                context['b_i'] = 'border-danger'
                errores.append("La imagen debe ser horizontal")
                context['publicado'] = None
                path = os.getcwd() + '/media/' + e.img.name
                os.remove(path)
                e.delete()

            elif e.img.size > 2 * 1024 * 1024 and not allow_big_size:
                errores.append("La imagen es demasiado grande")
                context['publicado'] = None
                path = os.getcwd() + '/media/' + e.img.name
                os.remove(path)
                e.delete()
            else:
                e.save()
                errores = None
                context['errores'] = None

        context['errores'] = errores

    return render(request, "freeketapp/plantilla_eventos.html", context)