from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from django.http import HttpResponse, Http404
from django.template import loader
from django.urls import NoReverseMatch

from freeketapp.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django import forms

import locale
import unicodedata
from cryptography.fernet import Fernet
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF


def index(request):
    template = loader.get_template("freeketapp/index.html")
    return HttpResponse(template.render())


@login_required(login_url='/login')
def crear_evento(request):
    context = {}
    return render(request, "freeketapp/plantilla_eventos.html", context)

@login_required(login_url='/login')
def evento_creado(request):
    context = {}
    if request.method == 'POST':
        # creamos al organizador del evento (provisional)
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            org = Organizador(nickname=request.user.username, id=request.user.id)
            org.save()
        else:
            org = org[0]
        titulo = request.POST.get('tituloEvento', '')
        context['titulo'] = titulo
        # formatear la fecha para que la bbdd la pueda almacenar
        fecha = request.POST.get('fechaEvento', '')
        fecha = fecha.split("-")
        fecha = fecha[2] + "-" + fecha[1] + "-" + fecha[0]
        hora = request.POST.get('horaEvento', '')
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
        url_id = str(unicodedata.normalize('NFD', url_id) \
                     .encode('ascii', 'ignore') \
                     .decode("utf-8"))
        # consultar si ya existe un evento con esa url
        e_number = Evento.objects.filter(url_id=url_id).count()
        # si existe, se añade una distinción a la nuva url
        if e_number >= 1:
            url_id = url_id + "_" + str(e_number)
        context['url_id'] = url_id
        # generamos clave para desencriptar entradas de evento
        key = Fernet.generate_key().decode()
        # uuid para evento
        id_evento = uuid.uuid4()
        # usuario que organiza el evento
        e = Evento(id=id_evento, titulo=titulo, url_id=url_id, fecha=fecha, hora=hora, numero_entradas=nentradas,
                   max_entradas_user=nmaxentradas,
                   organizador=org, key=key, ciudad=ciudad, direccion=direccion, cpostal=cpostal)
        e.save()

    return render(request, "freeketapp/evento_creado.html", context)


def pagina_evento(request, id):
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    id = id.lower()

    id = str(unicodedata.normalize('NFD', id) \
             .encode('ascii', 'ignore') \
             .decode("utf-8"))

    try:
        evento = Evento.objects.get(url_id=id)
        '''
        if evento.count() == 0:
            urlEvento = id.rsplit("_", 1)
            titEvento = ""
            idEvento = -1
            # la url viene en formato freeket.com/evento/esto-es-un-evento_id
            # con estas lineas procesamos el evento
            if len(urlEvento) > 1:
                idEvento = int(urlEvento[1])
                eventos = Evento.objects.filter(url_id=urlEvento[0])
                if eventos.count() > 1 and 0 <= idEvento < eventos.count():
                    evento = eventos[idEvento]
                else:
                    evento = None
            else:
                evento = None
        else:
            evento = evento[0]
        '''

        if evento is None:
            raise Http404("El evento no existe!")
        else:
            context = {}
            titulo_aux = evento.titulo
            context['titulo'] = titulo_aux
            # hay que actualizarlo cuando el usuario esté logeado, restanlo al max_entradas_user si ya ha comprado entradas antes
            context['nmax'] = evento.max_entradas_user
            eng_date_format = evento.fecha
            esp_date_format = eng_date_format.strftime("%d de %B de %Y")
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = id
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
    except Evento.DoesNotExist:
        raise Http404("El evento no existe!")
    except ValueError:
        raise Http404("El evento no existe!")
    return render(request, "freeketapp/pagina_evento.html", context)


@login_required(login_url='/login')
def compra_realizada(request):
    context = {}
    if request.method == 'POST':

        id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)
        print (id_confirmacion.count())
        nentradas = int(request.POST.get('nComprarEntradas', '1'))
        titulo = request.POST.get('nameEvento', '')
        id_evento = request.POST.get('idEvento', '')
        # provisional
        # u = Usuario.objects.get(id=1)
        # provisional
        e = Evento.objects.get(url_id=id_evento)
        if id_confirmacion.count() > 0:
            context['texto'] = "Necesitas confirmar el email antes de adquirir una entrada"
            url = '/evento/'+id_evento
            # pagina de confirmacion de email
            #return redirect(url)
        e.numero_entradas -= nentradas
        # controlamos que el máximo de entradas por usuario no sobrepase el número total de entradas que quedan
        if (e.max_entradas_user > e.numero_entradas):
            e.max_entradas_user = e.numero_entradas
        e.save()
        # uuid para cada nueva entrada
        for i in range(nentradas):
            id_entrada = uuid.uuid4()
            entrada = Entrada(usuario=request.user, evento=e, id=id_entrada)
            entrada.save()

        # big_code = pyqrcode.create(qr)
        # big_code.svg('freeketapp/static/freeketapp/uca-url.svg', scale=8)
    return render(request, "freeketapp/compra_realizada.html", context)


@login_required(login_url='/login')
def mostrar_entrada(request, id):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="entrada.pdf"'

    try:
        id_entrada = uuid.UUID(id).hex

        # falan comprobaciones de permisos de usuario
        entrada_exist = Entrada.objects.filter(id=id_entrada)
        if entrada_exist.count() == 0:
            raise Http404("La entrada no existe!")
        else:
            entrada = entrada_exist[0]
            # encriptando texto
            key = entrada.evento.key.encode()
            f_key = Fernet(key)
            txt_qr = f_key.encrypt(str(id_entrada).encode()).decode()
            qrw = QrCodeWidget(txt_qr)
            # Create the HttpResponse object with the appropriate PDF headers.
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="entrada.pdf"'
            p = canvas.Canvas(response)
            b = qrw.getBounds()

            w = b[2] - b[0]
            h = b[3] - b[1]

            d = Drawing(150, 150, transform=[150. / w, 0, 0, 150. / h, 0, 0])
            d.add(qrw)

            text = p.beginText(40, 750)
            text.setFont("Times-Roman", 14)
            text.textLine("Aqui tienes tu entrada para: ")
            text.textLine()
            text.setFont("Times-Roman", 28)
            text.textLine(entrada.evento.titulo)

            p.drawText(text)
            renderPDF.draw(d, p, 400, 650)

            p.showPage()
            p.save()
    except ValueError:
        raise Http404("La entrada noo existe!")
    return response


@login_required(login_url='/login')
def misentradas(request):
    ids = []
    titulos = []
    context = {}
    # usuario = Usuario.objects.get(id=1)
    entradas = Entrada.objects.filter(usuario=request.user)
    for i in entradas:
        ids.append(str(i.id))
        titulos.append(i.evento.titulo)
    context['ids'] = ids
    context['titulos'] = titulos
    context['elementos'] = zip(ids, titulos)
    return render(request, "freeketapp/misentradas.html", context)


def registro(request):
    context = {}
    logout(request)
    return render(request, "freeketapp/registro.html", context)


def send_confirmation_email(user):
    confirmation_code = ConfirmationCode.objects.get(usuario=user)
    title = "Freeket: confirmación de email"
    content = "127.0.0.1:8000/confirmation/" + str(confirmation_code.id) + "/" + user.username
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


def registro_realizado(request):
    context = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        duplicate_users = User.objects.filter(username=username)
        duplicated_email = User.objects.filter(email=email)
        if duplicate_users.exists():
            raise forms.ValidationError("Username is already registered!")
        elif duplicated_email.exists():
            raise forms.ValidationError("E-mail is already registered!")
        else:
            user = User.objects.create_user(username, email, password)
            user.first_name = name
            user.last_name = apellido
            user.save()
            # iniciar sesino del usuario
            # user = authenticate(request, username=username, password=password)
            # if user is not None:
            #    login(request, user)

            # mandar correo de confirmacion
            confirmation_code = ConfirmationCode(id=uuid.uuid4(), usuario=user)
            confirmation_code.save()
            send_confirmation_email(user)
    return render(request, "freeketapp/registro_realizado.html", context)


def my_login(request):
    context = {}
    logout(request)
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(request.POST.get('next', 'index'))
            else:
                context['texto'] = "Combinación usuario/contraseña incorrecta"
                return render(request, "freeketapp/login.html", context)
        else:
            return render(request, "freeketapp/login.html", context)
    except NoReverseMatch:
        return redirect('index')


def confirmation(request, id, user):
    context = {}
    try:
        user_object = User.objects.get(username=user)
        id_confirmacion = ConfirmationCode.objects.get(usuario=user_object)

        if (str(id_confirmacion.id) == id):
            context['texto'] = "Email confirmado correctamente!"
            user_object.save()
            # no lo necesitamos mas
            id_confirmacion.delete()
        else:
            context['texto'] = "Fallo en la confirmación del email"
    except ValueError:
        raise Http404("Codigo incorrecto")
    return render(request, "freeketapp/confirmacion.html", context)


@login_required(login_url='/login')
def reset_password(request):
    context = {}
    if request.method == 'POST':
        password = request.POST.get('oldpassword')
        user = authenticate(request, username=request.user, password=password)
        if user is not None:
            # comprobar formulario
            new_password = request.POST.get('password')
            user.set_password(new_password)
            user.save()
            context['texto'] = "La contraseña se ha actualizado correctamente."
        else:
            context['texto'] = "La contraseña actual proporcionada es incorrecta"

    return render(request, "freeketapp/reset_password.html", context)
