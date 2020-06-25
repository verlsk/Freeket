from datetime import datetime
from datetime import timedelta
from io import BytesIO
import time
import pathlib
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render, redirect
from django.core import serializers
from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.urls import NoReverseMatch

from freeketapp.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import locale
import unicodedata
from cryptography.fernet import Fernet
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from django.db.models import Count, Q
import json
import threading
from time import time, localtime, strftime
import os


# import pyzbar.pyzbar as pyzbar


def index(request):
    context = {}
    if request.user.is_authenticated:

        context['islogged'] = 'y'
        context['name'] = request.user.username
        context['profile'] = request.session['profile']
        if context['profile'] == 'org':
            return redirect('organizador')
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True

    else:
        context['islogged'] = 'n'

    eventos = Evento.objects.order_by('-visitas')

    eventos = eventos.filter(fecha__gte=strftime("%Y-%m-%d", localtime(time())), numero_entradas_actual__gte=1)[:3]

    context['eventos'] = eventos
    return render(request, "freeketapp/base.html", context)


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

        try:
            img = request.FILES['imgEvento']
        except:
            img = 'm/default.jpg'
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
            elif e.img.size > 2 * 1024 * 1024:
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


def pagina_evento(request, id_evento):
    context = {}
    if request.user.is_authenticated:
        context['name'] = request.user.username
        context['islogged'] = 'y'
        context['profile'] = request.session['profile']
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True
    else:
        context['islogged'] = 'n'
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    id_evento = id_evento.lower()
    errores = []
    id_evento = str(unicodedata.normalize('NFD', id_evento)
                    .encode('ascii', 'ignore')
                    .decode("utf-8"))

    try:
        evento = Evento.objects.get(url_id=id_evento)
        if request.method == 'POST':

            id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)
            nentradas = int(request.POST.get('nComprarEntradas', '1'))
            id_evento = request.POST.get('idEvento', '')

            e = evento
            entradas_evento_usuario = Entrada.objects.filter(usuario=request.user, evento=e).count()
            if request.user.id == evento.organizador.id or context['profile'] == 'org':
                errores.append("Como organizador del evento, no puedes adquirir entradas")
            if id_confirmacion.count() > 0:
                errores.append("Necesitas confirmar el email antes de adquirir una entrada")
            if nentradas > e.numero_entradas_actual and entradas_evento_usuario + nentradas <= e.max_entradas_user != 0:
                strerror = "No hay tantas entradas disponibles. Lo máximo que puedes adquirir es " + str(
                    e.numero_entradas_actual)
                errores.append(strerror)

            if entradas_evento_usuario == e.max_entradas_user and e.max_entradas_user != 0:
                errores.append("Ya has adquirido el máximo de entradas para este evento")
            elif entradas_evento_usuario + nentradas > e.max_entradas_user != 0:
                strerror = "No puedes adquirir tantas entradas. El máximo de entradas que te quedan por adquirir es " + str(
                    e.max_entradas_user - entradas_evento_usuario)
                errores.append(strerror)

            # controlamos que el máximo de entradas por usuario no sobrepase el número total de entradas que quedan

            if len(errores) == 0:
                # uuid para cada nueva entrada
                for i in range(nentradas):
                    id_entrada = uuid.uuid4()
                    entrada = Entrada(usuario=request.user, evento=e, id=id_entrada)
                    entrada.save()
                    t = threading.Thread(target=enviar_entrada, args=(entrada,), kwargs={})
                    t.setDaemon(True)
                    t.start()
                # actualizacion del numero de entradas
                e.numero_entradas_actual -= nentradas
                e.save()
                context['adquiridas'] = 'y'
            context['errores'] = errores
        if evento is None:
            raise Http404("El evento no existe!")
        else:
            if request.method == 'GET':
                evento.visitas += 1
                evento.save()

            titulo_aux = evento.titulo
            context['titulo'] = titulo_aux
            context['img'] = evento.img.url
            if evento.max_entradas_user != 0:
                context['nmax'] = evento.max_entradas_user
            else:
                context['nmax'] = 15
            eng_date_format = evento.fecha
            if eng_date_format < date.today():
                context['mostrarcomprar'] = 'n'
            else:
                context['mostrarcomprar'] = 'y'

            if evento.numero_entradas_actual == 0:
                context['mostrarcomprar'] = 'n'

                if context['islogged'] == 'y':
                    context['listaespera'] = 'y'
                    l_espera = ListaEspera.objects.filter(evento=evento, usuario=request.user)

                    if l_espera.count() > 0:
                        context['listaespera'] = 'disabled'

            esp_date_format = eng_date_format.strftime("%A %d de %B de %Y")
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = id_evento
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
            context['descripcion'] = evento.descripcion

    except Evento.DoesNotExist:
        raise Http404("El evento no existe!")
    except ValueError:
        raise Http404("El evento no existe!")

    return render(request, "freeketapp/pagina_evento.html", context)


# Generacion de PDF con entrada
def get_entrada(entrada, p):
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    # encriptando texto
    key = entrada.evento.key.encode()
    f_key = Fernet(key)

    txt_qr = f_key.encrypt(str(entrada.id).encode()).decode()

    qrw = QrCodeWidget(txt_qr)
    # Create the HttpResponse object with the appropriate PDF headers.

    b = qrw.getBounds()

    w = b[2] - b[0]
    h = b[3] - b[1]

    d = Drawing(150, 150, transform=[150. / w, 0, 0, 150. / h, 0, 0])
    d.add(qrw)

    path = os.getcwd()

    # path += entrada.evento.img.url

    img_url = entrada.evento.img.url
    path += img_url
    img_w = entrada.evento.img.width
    img_h = entrada.evento.img.height

    new_h = 330
    new_w = new_h * (img_w / img_h)

    if new_w > 530:
        new_w = 530
        new_h = (img_h * new_w) / img_w
    x_margin = (600 - new_w) / 2
    p.drawImage(path, x_margin, 200, height=new_h, width=new_w, mask='auto')

    path = os.getcwd()

    path += "/media/m/logo4.png"

    p.drawImage(path, 250, 70, height=20, width=100, mask='auto')

    titulo_1 = ""
    titulo_2 = ""
    cut = 0
    if len(entrada.evento.titulo) > 32:
        for i in entrada.evento.titulo[26:]:
            if i == ' ':
                break
            cut += 1

        titulo_1 = entrada.evento.titulo[:26 + cut]
        titulo_2 = entrada.evento.titulo[26 + cut + 1:]
    else:
        titulo_1 = entrada.evento.titulo
    text = p.beginText(x_margin, 770)
    text.setFont("Times-Roman", 22)
    text.textLine(titulo_1)
    text.textLine(titulo_2)
    text.setFont("Times-Roman", 14)
    eng_date_format = entrada.evento.fecha
    esp_date_format = eng_date_format.strftime("%A %d de %B de %Y")
    fecha = esp_date_format
    text.textLine(fecha)
    text.textLine(entrada.evento.hora)
    text.setFont("Times-Roman", 11)
    text.textLine(entrada.evento.ciudad)
    text.textLine(entrada.evento.direccion)
    text.textLine(entrada.evento.cpostal)

    p.drawText(text)

    text = p.beginText(13, 27)
    text.setFont("Times-Roman", 8)
    text.textLine("Entrada adquirida por medio de Freeket. Ante cualquier duda o problema "
                  "relacionado con la asistencia a este "
                  "evento, contacte con el soporte de Freeket o con el organizador")
    text.textLine("del evento. Esperamos que disfrute de la experiencia.")

    p.drawText(text)

    p.setStrokeColorRGB(0.427, 0.011, 0.313)
    p.rect(x=10, y=10, width=575, height=820, stroke=True)

    return p, d


# Envio de entrada por email
def enviar_entrada(entrada):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p, d = get_entrada(entrada, p)
    renderPDF.draw(d, p, 400, 650)
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    email = EmailMessage(
        'Aquí tienes tu entrada!', 'Que te lo pases bien.', 'freeketmail@gmail.com', [entrada.usuario.email])
    email.attach('entrada.pdf', pdf, 'application/pdf')
    email.send()


@login_required(login_url='/login')
def mostrar_entrada(request, id_entrada):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="entrada.pdf"'

    try:
        id_entrada = uuid.UUID(id_entrada).hex

        entrada_exist = Entrada.objects.filter(id=id_entrada)
        if entrada_exist.count() == 0:
            raise Http404("La entrada no existe!")
        else:
            entrada = entrada_exist[0]
            if entrada.usuario == request.user:
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="entrada.pdf"'

                p = canvas.Canvas(response)
                p, d = get_entrada(entrada, p)

                renderPDF.draw(d, p, 400, 650)

                p.showPage()
                p.save()
            else:
                raise Http404("La entrada no existe!")
    except ValueError:
        raise Http404("La entrada no existe")
    return response


@login_required(login_url='/login')
def misentradas(request):
    ids = []
    evs = []
    fechas = []
    context = {}
    # usuario = Usuario.objects.get(id=1)
    entradas = Entrada.objects.filter(usuario=request.user)
    for i in entradas:
        ids.append(i)
        evs.append(i.evento)
        fechas.append(i.fecha_adquisicion.strftime("%d-%m-%Y"))

    evs.reverse()
    ids.reverse()
    fechas.reverse()
    context['islogged'] = 'y'
    context['name'] = request.user.username
    context['ids'] = ids
    context['elementos'] = zip(ids, evs, fechas)
    context['profile'] = request.session['profile']
    if context['profile'] == 'org':
        return redirect('organizador')
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    return render(request, "freeketapp/misentradas.html", context)


def registro(request):
    context = {'showform': True}
    errores = []
    context['errores'] = errores
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':

        user_type = request.POST.get('user_type')
        username = request.POST.get('username').lower()
        name = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        rep_password = request.POST.get('repPassword')
        duplicate_users = User.objects.filter(username=username)
        duplicated_email = User.objects.filter(email=email)
        org_direccion = request.POST.get('orgDireccion')
        org_ciudad = request.POST.get('orgCiudad')
        org_cpostal = request.POST.get('orgCPostal')
        org_telefono = request.POST.get('orgTelefono')
        ck_org = request.POST.get('ckOrg')
        ck_datos = request.POST.get('ckDatos')
        if (user_type == 'org' or user_type == 'both') and org_direccion == '':
            errores.append("Para organizadores, la dirección es necesaria")
            context['b_dir'] = "border-danger"
        elif org_direccion != '':
            context['orgDireccion'] = org_direccion

        if (user_type == 'org' or user_type == 'both') and ck_org is None:
            errores.append("Tienes que aceptar la política de uso de datos de los asistentes")

        if (user_type == 'org' or user_type == 'both') and org_ciudad == '':
            errores.append("Para organizadores, la ciudad es necesaria")
            context['b_ciu'] = "border-danger"
        elif org_ciudad != '':
            context['orgCiudad'] = org_ciudad

        if (user_type == 'org' or user_type == 'both') and org_cpostal == '':
            errores.append("Para organizadores, el código postal es necesario")
            context['b_cp'] = "border-danger"
        elif org_ciudad != '':
            context['orgCPostal'] = org_ciudad

        if (user_type == 'org' or user_type == 'both') and org_telefono == '':
            errores.append("Para organizadores, el teléfono es necesario")
            context['b_tel'] = "border-danger"
        elif org_telefono != '':
            context['orgTelefono'] = org_telefono

        if duplicate_users.exists():
            errores.append("Nombre de usuario existente")
            context['b_u'] = "border-danger"
        else:
            context["username"] = username
        if duplicated_email.exists():
            errores.append("Email registrado por otro usuario")
            context['b_e'] = "border-danger"
        else:
            context["email"] = email

        if len(password) < 8:
            errores.append("La contraseña es demasiado corta")
            context['b_p'] = "border-danger"
            context["name"] = name
            context["surname"] = apellido
        elif password != rep_password:
            errores.append("Las contraseñas no coinciden")
            context['b_p'] = "border-danger"
            context["name"] = name
            context["surname"] = apellido
        if username == '':
            errores.append("El nombre de usuario no puede estar vacío")
            context['b_u'] = "border-danger"

        if email == '':
            errores.append("El email no puede estar vacío")
            context['b_e'] = "border-danger"

        if password == '':
            errores.append("La contraseña no puede estar vacía")
            context['b_p'] = "border-danger"
        if ck_datos is None:
            errores.append(
                "Es obligatorio que aceptes nuestra política de tratamiento de datos personales para registrate en el sistema")
            context['b_ck'] = "border-danger"
        if len(errores) > 0:
            context['errores'] = errores
        else:

            context['showform'] = False
            context['errores'] = None
            context[
                'texto'] = "Te has registrado correctamente. Revisa tu bandeja de correo electrónico, ya que te hemos mandado un email de confirmación. "
            user = User.objects.create_user(username, email, password)
            user.first_name = name
            user.last_name = apellido
            if user_type == 'org':
                org = Organizador(nickname=username, id=user.id, exclusive_org=True, direccion=org_direccion,
                                  ciudad=org_ciudad, cpostal=org_cpostal, telefono=org_telefono)
                org.save()
            elif user_type == 'both':
                org = Organizador(nickname=username, id=user.id, exclusive_org=False)
                org.save()
            user.save()

            # mandar correo de confirmacion
            confirmation_code = ConfirmationCode(id=uuid.uuid4(), usuario=user)
            confirmation_code.save()
            send_confirmation_email(user)
    else:
        context['errores'] = None
    return render(request, "freeketapp/registro.html", context)


def send_confirmation_email(user):
    confirmation_code = ConfirmationCode.objects.get(usuario=user)
    title = "Freeket: Confirmación de email"
    content = "Bienvenido a Freeket, " + user.username + "!\n\n"
    content += "Para confimar tu email y poder adquirir entradas, accede a la siguiente página: "
    content += "http://freeket.es/confirmation/" + str(confirmation_code.id) + "/" + user.username
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


def my_login(request):
    context = {}
    if request.user.is_authenticated:
        logout(request)
    try:
        if request.method == 'POST':
            user_type = request.POST.get('user_type')

            username = request.POST.get('username')
            if username is not None:
                username = username.lower()
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:

                if user_type == 'org':
                    org = Organizador.objects.filter(nickname=username)
                    if org.count() > 0:
                        request.session['profile'] = 'org'
                        login(request, user)
                    else:
                        context['texto'] = "No estás registrado como organizador"
                        return render(request, "freeketapp/login.html", context)
                elif user_type == 'assist':
                    org = Organizador.objects.filter(nickname=username)

                    if org.count() > 0:

                        if org[0].exclusive_org:
                            context['texto'] = "No estás registrado como asistente"
                            return render(request, "freeketapp/login.html", context)

                    request.session['profile'] = 'assist'
                    login(request, user)
                else:
                    context['texto'] = "Perfil de usuario incorrecto"
                    return render(request, "freeketapp/login.html", context)

                return redirect(request.POST.get('next', 'index'))
            else:
                if request.POST.get('next') is not None:
                    context['texto'] = "Combinación usuario/contraseña incorrecta"
                return render(request, "freeketapp/login.html", context)
        else:
            return render(request, "freeketapp/login.html", context)
    except NoReverseMatch:
        return redirect('index')


def confirmation(request, id_confirmacion_url, user):
    context = {}

    try:
        user_object = User.objects.get(username=user)
        id_confirmacion = ConfirmationCode.objects.get(usuario=user_object)
        if str(id_confirmacion.id) == id_confirmacion_url:
            context['texto'] = "Email confirmado correctamente!"
            # no lo necesitamos mas
            id_confirmacion.delete()
            login(request, user_object)

        else:
            context['texto'] = "Fallo en la confirmación del email"

        if request.user.is_authenticated:
            context['islogged'] = 'y'
            context['name'] = request.user.username
            org = Organizador.objects.filter(id=request.user.id)
            if org.count() == 0:
                context['org'] = False
                request.session['profile'] = 'assist'
            else:
                context['org'] = True

                if org[0].exclusive_org:
                    context['assist'] = False
                    request.session['profile'] = 'org'
                else:
                    context['assist'] = True
                    request.session['profile'] = 'assist'
            context['profile'] = request.session['profile']
            login(request, user_object)
        else:
            context['islogged'] = 'n'
    except:
        raise Http404("Codigo incorrecto")
    return render(request, "freeketapp/confirmacion.html", context)


@login_required(login_url='/login')
def reset_password(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'r_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    errores = []
    id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)

    if id_confirmacion.count() > 0:
        context['send'] = 'y'
    if request.method == 'POST':
        password = request.POST.get('oldpassword')
        user = authenticate(request, username=request.user, password=password)
        if user is not None:
            new_password = request.POST.get('password')
            rep_password = request.POST.get('repPassword')
            if new_password != rep_password:
                errores.append("Las contraseñas no coinciden")
            if len(new_password) < 8:
                errores.append("La contraseña es demasiado corta")
            if password == new_password:
                errores.append("La contraseña nueva es igual que la antigua. Por favor, cambia de contraseña")

            context['errores'] = errores

            if len(errores) == 0:
                user.set_password(new_password)
                user.save()
                user = authenticate(request, username=request.user, password=new_password)
                prof = context['profile']
                login(request, user)
                request.session['profile'] = prof
                context['texto'] = "La contraseña se ha actualizado correctamente."
                context['errores'] = None
        else:
            errores.append("La contraseña actual proporcionada es incorrecta")
            context['errores'] = errores
    else:
        context['errores'] = None
    return render(request, "freeketapp/reset_password.html", context)


def send_forgot_password_email(user, password):
    title = "Freeket: Reestablecimiento de contraseña"
    content = "Tus nuevos credenciales son: \nUsuario: " + user.username + "\nContraseña: " + password
    content += "\nInicia sesión y accede a \"Mi perfil\" para modificarla."
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


def forgot_password_form(request):
    context = {}
    if request.user.is_authenticated:
        logout(request)
    if request.method == 'POST':
        email = request.POST.get('email').replace(" ", "")
        user = User.objects.filter(email=email)
        if user.count() > 0:
            user = user[0]
            # generando nueva contrasena a partir de un uuid
            password = str(uuid.uuid4()).split("-")[0]
            user.set_password(password)
            user.save()
            send_forgot_password_email(user, password)
            context[
                'texto'] = 'Te hemos mandado un email con tu nueva contraseña. Accede a tu cuenta y modifícala en el ' \
                           'apartado \"Mi perfil\" '
        else:
            context['texto'] = 'Tu email no está asociado a ninguna cuenta existente'
    return render(request, "freeketapp/forgot_password_form.html", context)


@login_required(login_url='/login')
def mi_perfil(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'm_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    errores = []
    id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)

    if id_confirmacion.count() > 0:
        context['send'] = 'y'

    if request.method == 'POST':
        # validar
        name = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        org_direccion = request.POST.get('orgDireccion')
        org_ciudad = request.POST.get('orgCiudad')
        org_cpostal = request.POST.get('orgCPostal')
        org_telefono = request.POST.get('orgTelefono')
        ck_org = request.POST.get('ckOrg')
        if context['org']:

            if org_direccion == '':
                errores.append("Para organizadores, la dirección es necesaria")
                context['b_dir'] = "border-danger"
            elif org_direccion != '':
                context['orgDireccion'] = org_direccion

            if org_ciudad == '':
                errores.append("Para organizadores, la ciudad es necesaria")
                context['b_ciu'] = "border-danger"
            elif org_ciudad != '':
                context['orgCiudad'] = org_ciudad

            if org_cpostal == '':
                errores.append("Para organizadores, el código postal es necesario")
                context['b_cp'] = "border-danger"
            elif org_ciudad != '':
                context['orgCPostal'] = org_ciudad

            if org_telefono == '':
                errores.append("Para organizadores, el teléfono es necesario")
                context['b_tel'] = "border-danger"
            elif org_telefono != '':
                context['orgTelefono'] = org_telefono

        user = authenticate(request, username=request.user, password=password)

        if user is not None:
            request.user.first_name = name
            request.user.last_name = apellido
            duplicated_email = User.objects.filter(email=email.lower())
            if duplicated_email.count() == 1 and duplicated_email[0] != request.user:
                errores.append("Este email pertenece a otro usuario")
            elif duplicated_email.count() > 1:
                errores.append("Este email pertenece a otro usuario")
            elif email == '':
                errores.append("El campo \"Email\" no puede estar vacío")
            else:
                if request.user.email != email.lower():
                    request.user.email = email.lower()

                    context['texto'] = "Datos actualizados correctamente. Te hemos mandado un email de confirmación"
                    errores = None
                    # mandar correo de confirmacion
                    confirmation_code = ConfirmationCode(id=uuid.uuid4(), usuario=request.user)
                    confirmation_code.save()
                    send_confirmation_email(request.user)
                else:
                    context['texto'] = "Datos actualizados correctamente."
                    errores = None
                request.user.save()
                if context['org']:
                    org_local = Organizador.objects.get(id=request.user.id)
                    org_local.direccion = org_direccion
                    org_local.ciudad = org_ciudad
                    org_local.cpostal = org_cpostal
                    org_local.telefono = org_telefono
                    org_local.save()
        else:
            errores.append("Contraseña incorrecta")
    else:
        errores = None
    context['errores'] = errores
    context['nombre'] = request.user.first_name
    context['apellido'] = request.user.last_name
    context['email'] = request.user.email
    if org.count() > 0:
        org = org[0]
        context['orgDireccion'] = org.direccion
        context['orgCiudad'] = org.ciudad
        context['orgCPostal'] = org.cpostal
        context['orgTelefono'] = org.telefono

    return render(request, "freeketapp/mi_perfil.html", context)


@login_required(login_url='/login')
def confirmar_email(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'c_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    id_confirmacion = ConfirmationCode.objects.filter(usuario_id=request.user.id)

    if request.method == 'POST':
        if id_confirmacion.count() > 0:
            send_confirmation_email(request.user)
            context['texto'] = "Te hemos mandado un email de confirmación"
            context['send'] = 'n'
    else:
        if id_confirmacion.count() > 0:
            context['send'] = 'y'
        else:
            context['texto'] = "Email confirmado!"
            context['send'] = 'n'
    return render(request, "freeketapp/confirmar_email.html", context)


@login_required(login_url='/login')
def cerrar_sesion(request):
    context = {}
    logout(request)
    return redirect('index')


@login_required(login_url='/login')
def gestionar_eventos(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        # redirect
        pass
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    org = Organizador.objects.filter(nickname=request.user.username)

    if org.count() == 1:
        org = org[0]
        eventos = list(Evento.objects.filter(organizador=org))
        if len(eventos) > 0:
            context['mostrareventos'] = 'y'
            eventos.reverse()
            context['eventos'] = eventos
        else:
            context['mostrareventos'] = 'n'

    else:
        context['mostrareventos'] = 'n'
        # no hay eventos que mostrar

    return render(request, "freeketapp/gestionar_eventos.html", context)


@login_required(login_url='/login')
def gestionar_eventos_evento(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'e_active': "btnSideActive"}

    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")

        numero_entradas_inicial = evento.numero_entradas_inicial
        numero_entradas_actual = evento.numero_entradas_actual

        entradas = Entrada.objects.filter(evento=evento).values('fecha_adquisicion').annotate(
            total=Count('fecha_adquisicion')).order_by('fecha_adquisicion')
        labels = []
        data = []

        delta = timedelta(days=1)
        start_date = evento.fecha_creacion
        end_date = date.today()

        if entradas.count() > 0:
            end_date = entradas[0]['fecha_adquisicion']

        while start_date < end_date:
            esp_date_format = start_date.strftime("%d-%m-%Y")
            labels.append(esp_date_format)
            data.append(0)
            start_date += delta
        if entradas.count() > 0:
            start_date = entradas[0]['fecha_adquisicion']
            if evento.fecha >= date.today():
                end_date = date.today()
            else:
                end_date = evento.fecha
            contador_entradas = 0
            while start_date <= end_date:
                data_to_append = 0
                if start_date == entradas[contador_entradas]['fecha_adquisicion']:
                    data_to_append = entradas[contador_entradas]['total']
                    if contador_entradas + 1 < entradas.count():
                        contador_entradas += 1

                esp_date_format = start_date.strftime("%d-%m-%Y")
                labels.append(esp_date_format)
                data.append(data_to_append)
                start_date += delta

        context['visitas'] = evento.visitas
        context['n_entradas'] = str(numero_entradas_actual)
        context['n_entradas_inicial'] = str(numero_entradas_inicial)
        context['n_entradas_adquiridas'] = str(numero_entradas_inicial - numero_entradas_actual)
        context['data'] = data
        context['labels'] = json.dumps(labels)
        context['id_evento'] = id_evento

    except Evento.DoesNotExist:
        raise Http404("El evento no existe")

    return render(request, "freeketapp/gestionar_eventos_evento.html", context)


def enviar_email_cambios(evento, text):
    entradas = Entrada.objects.filter(evento=evento).values('usuario').annotate(c=Count('usuario'))

    for i in entradas:
        user = User.objects.get(id=i['usuario'])
        title = "Cambios en tu evento"
        content = "Hola, " + user.username + ":\n"
        content += "Te escribimos para comunicarte que ha habido cambios en el evento \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir."
        if text != '':
            content += "\nAquí tienes una nota del organizador:\n\n\t" + text
        content += "\nPuedes consultar la nueva información en: freeket.es/evento/" + evento.url_id

        send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)

    invitado = User.objects.get(username='invitado')
    entradas = Entrada.objects.filter(usuario=invitado)
    for i in entradas:
        title = "Cambios en tu evento"
        content = "Hola: \n"
        content += "Te escribimos para comunicarte que ha habido cambios en el evento \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir."
        if text != '':
            content += "\nAquí tienes una nota del organizador:\n" + text
        content += "\nPuedes consultar la nueva información en: freeket.es/evento/" + evento.url_id

        send_mail(title, content, 'freeketmail@gmail.com', [i.aux_email], fail_silently=False)


@login_required(login_url='/login')
def gestionar_eventos_modificar(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'id_evento': id_evento,
               'profile': request.session['profile'], 'm_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    errores = []
    cambios = False
    mandar_email = False
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")

        if request.method == 'POST':
            titulo = request.POST.get('tituloEvento', '')
            if titulo != str(evento.titulo):
                evento.titulo = titulo
                cambios = True
            # formatear la fecha para que la bbdd la pueda almacenar

            try:
                img = request.FILES['imgEvento']
                evento.img = img
                if evento.img.width < evento.img.height:
                    context['b_i'] = 'border-danger'
                    errores.append("La imagen debe ser horizontal")
                    context['publicado'] = None
                    path = os.getcwd() + '/media/' + evento.img.name
                    os.remove(path)
                    evento.delete()
            except:
                pass
            descripcion = request.POST.get('descripcion', '')
            if descripcion == '':
                context['b_det'] = 'border-danger'
                errores.append("Escribe una descripción acerca de tu evento")
            elif len(descripcion) > 20000:
                context['b_det'] = 'border-danger'
                errores.append("Tu descripción es demasiado larga")
            else:
                if str(evento.descripcion) != descripcion:
                    cambios = True
                    evento.descripcion = descripcion

            fecha = request.POST.get('fechaEvento', '')
            fecha = validate_date(fecha)
            if not fecha:
                context['b_f'] = 'border-danger'
                errores.append("Formato de fecha incorrecto")
            else:

                if str(fecha) != str(evento.fecha):

                    evento.fecha = fecha
                    context['fecha'] = datetime.strptime(evento.fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
                    cambios = True
                    mandar_email = True
                else:
                    context['fecha'] = evento.fecha.strftime("%d-%m-%Y")
            hora = request.POST.get('horaEvento', '')
            if not isTimeFormat(hora):
                context['b_h'] = 'border-danger'
                errores.append("Formato de hora incorrecto")

            else:

                if hora != evento.hora:
                    evento.hora = hora
                    cambios = True
                    mandar_email = True

            nentradas = request.POST.get('nEntradas', '')
            if str(nentradas) != str(evento.numero_entradas_actual):
                evento.numero_entradas_inicial = evento.numero_entradas_inicial - evento.numero_entradas_actual + int(
                    nentradas)
                evento.numero_entradas_actual = nentradas
                cambios = True

            nmaxentradas = request.POST.get('nMaxEntradas', '')
            if nmaxentradas != str(evento.max_entradas_user):
                evento.max_entradas_user = nmaxentradas
                cambios = True
            ciudad = request.POST.get('ciudad', '')
            if str(ciudad) != str(evento.ciudad):
                evento.ciudad = ciudad
                cambios = True
                mandar_email = True
            cpostal = request.POST.get('cpostal', '')
            if cpostal != str(evento.cpostal):
                evento.cpostal = cpostal
                cambios = True
                mandar_email = True
            direccion = request.POST.get('direccion', '')
            if direccion != str(evento.direccion):
                evento.direccion = direccion
                cambios = True
                mandar_email = True

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

            nota_informativa = ''
            if mandar_email:
                nota_informativa = request.POST.get('notaInformativa', '')
                if nota_informativa == '':
                    errores.append(
                        "Debido a los cambios realizados, es necesario que escribas una nota informativa a tus asistentes")
                    context['b_not'] = 'border-danger'
            context['errores'] = errores
            if len(errores) == 0:
                context['errores'] = None
                if cambios == True:

                    context['publicado'] = True

                    evento.save()

                    if mandar_email:
                        # mandar email
                        t = threading.Thread(target=enviar_email_cambios, args=(evento, nota_informativa), kwargs={})
                        t.setDaemon(True)
                        t.start()



        else:

            context['fecha'] = evento.fecha.strftime("%d-%m-%Y")
        context['titulo'] = evento.titulo

        context['hora'] = evento.hora
        context['nentradas'] = evento.numero_entradas_actual
        context['ciudad'] = evento.ciudad
        context['direccion'] = evento.direccion
        context['descripcion'] = evento.descripcion
        context['cpostal'] = evento.cpostal
        context['nmax'] = evento.max_entradas_user
    except Evento.DoesNotExist:
        raise Http404("El evento no existe")
    except TypeError:
        errores.append("Campos obligatorios vacíos o erróneos")
        context['errores'] = errores
    return render(request, "freeketapp/gestionar_eventos_modificar.html", context)


def enviar_email_informativo(evento, text):
    entradas = Entrada.objects.filter(evento=evento).values('usuario').annotate(c=Count('usuario'))

    for i in entradas:
        user = User.objects.get(id=i['usuario'])
        title = "Notificación acerca de tu evento"
        content = "Hola, " + user.username + ":\n"
        content += "Tienes una nota informativa de parte del organizador del evento: \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir:"

        content += "\n\n    \"" + text + "\""

        send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)

    invitado = User.objects.get(username='invitado')
    entradas = Entrada.objects.filter(usuario=invitado)
    for i in entradas:
        title = "Notificación acerca de tu evento"
        content = "Hola: \n"
        content += "Tienes una nota informativa de parte del organizador del evento: \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir:"

        content += "\n\n    \"" + text + "\""

        send_mail(title, content, 'freeketmail@gmail.com', [i.aux_email], fail_silently=False)


def enviar_email_invitaciones(evento, emails):
    user = User.objects.get(username='invitado')
    for i in emails:
        if i != '' and i is not None:
            id_entrada = uuid.uuid4()
            entrada = Entrada(usuario=user, evento=evento, id=id_entrada, aux_email=i)
            entrada.save()
            if evento.numero_entradas_actual > 0:
                evento.numero_entradas_actual -= 1
                evento.save()

            # GENERAMOS PDF CON ENTRD
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p, d = get_entrada(entrada, p)
            renderPDF.draw(d, p, 400, 650)
            p.showPage()
            p.save()
            pdf = buffer.getvalue()
            buffer.close()
            message = "Hola!\n\t El organizador del evento: \"" + evento.titulo + "\" te ha enviado una invitación.\n"
            message += "\tLa encontrarás junto a este email.\n\tEsperamos que disfrutes del evento."
            message += "\tPuedes encontrar información adicional acerca de este evento en: freeket.es/evento/" + evento.url_id
            email = EmailMessage(
                'Has recibido una invitación para un evento Freeket!', message, 'freeketmail@gmail.com',
                [i])
            email.attach('entrada.pdf', pdf, 'application/pdf')
            email.send()


@login_required(login_url='/login')
def gestionar_eventos_notificacion(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'id_evento': id_evento,
               'profile': request.session['profile'], 'n_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    errores = []
    context['enviado'] = False
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")
        if request.method == 'POST':
            mensaje = request.POST.get('notaInformativa', '')
            if mensaje == '':
                errores.append("El mensaje está vacío")
                context['errores'] = errores

            else:
                evento = Evento.objects.get(url_id=id_evento)
                context['enviado'] = True
                t = threading.Thread(target=enviar_email_informativo, args=(evento, mensaje), kwargs={})
                t.setDaemon(True)
                t.start()
    except TypeError:
        raise Http404("No encontrado")

    return render(request, "freeketapp/gestionar_eventos_notificacion.html", context)


@login_required(login_url='/login')
def gestionar_eventos_invitaciones(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'id_evento': id_evento,
               'profile': request.session['profile'], 'i_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    errores = []
    context['enviado'] = False
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")
        if request.method == 'POST':
            emails = request.POST.get('emailsInvitaciones', '').split(" ")
            if emails == '' or emails is None:
                errores.append("No hay ninguna dirección de email válida")
                context['errores'] = errores

            else:
                evento = Evento.objects.get(url_id=id_evento)
                context['enviado'] = True
                t = threading.Thread(target=enviar_email_invitaciones, args=(evento, emails), kwargs={})
                t.setDaemon(True)
                t.start()
    except TypeError:
        raise Http404("No encontrado")

    return render(request, "freeketapp/gestionar_eventos_invitaciones.html", context)


def enviar_email_cancelar(evento):
    entradas = Entrada.objects.filter(evento=evento).values('usuario').annotate(c=Count('usuario'))

    for i in entradas:
        user = User.objects.get(id=i['usuario'])
        title = "ATENCIÓN: Evento cancelado"
        content = "Hola, " + user.username + ":\n"
        content += "El organizador del evento: \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir, lo ha cancelado. Sentimos lo ocurrido."

        send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)

    invitado = User.objects.get(username='invitado')
    entradas = Entrada.objects.filter(usuario=invitado)
    for i in entradas:
        title = "ATENCIÓN: Evento cancelado"
        content = "Hola: \n"
        content += "El organizador del evento: \"" + evento.titulo + "\""
        content += ", al que tenías previsto asistir, lo ha cancelado. Sentimos lo ocurrido."

        send_mail(title, content, 'freeketmail@gmail.com', [i.aux_email], fail_silently=False)

    path = os.getcwd() + evento.img.url

    if path.split("/")[-1] != "default.jpg":
        os.remove(path)
    evento.delete()


@login_required(login_url='/login')
def gestionar_eventos_cancelar(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'id_evento': id_evento,
               'profile': request.session['profile'], 'c_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True
        if request.method == 'POST':
            t = threading.Thread(target=enviar_email_cancelar, args=(evento,), kwargs={})
            t.setDaemon(True)
            t.start()

            return redirect('gestionar_eventos')
    except:
        raise Http404("El evento no existe")
    return render(request, "freeketapp/gestionar_eventos_cancelar.html", context)


@login_required(login_url='/login')
def gestionar_eventos_asistentes(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'id_evento': id_evento,
               'profile': request.session['profile'], 'l_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False

    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

    evento = Evento.objects.get(url_id=id_evento)
    # comprobar propietario del evento
    if evento.organizador.nickname != request.user.username:
        raise Http404("El evento no existe")
    users = []
    counts = []
    entradas = Entrada.objects.filter(evento=evento).values('usuario').annotate(c=Count('usuario'))
    for i in entradas:
        user = User.objects.get(id=i['usuario'])
        users.append(user)
        counts.append(i['c'])

    context['asistentes'] = zip(users, counts)

    return render(request, "freeketapp/gestionar_eventos_asistentes.html", context)


def eventos(request):
    context = {'islogged': 'y', 'name': request.user.username}
    if not request.user.is_authenticated:
        context['islogged'] = 'n'
    else:
        context['profile'] = request.session['profile']
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True

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


@login_required(login_url='/login')
def registro_asistente(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'a_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:

        context['org'] = False
    else:
        org = org[0]
        context['org'] = True
        if org.exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

    if request.method == 'POST':
        org.exclusive_org = False
        org.save()
        request.session['profile'] = 'assist'
        return redirect('index')

    return render(request, "freeketapp/registro_asistente.html", context)


@login_required(login_url='/login')
def registro_organizador(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile'],
               'o_active': "btnSideActive"}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

    if request.method == 'POST':
        tmp_org = Organizador.objects.filter(id=request.user.id)
        if tmp_org.count() > 0:
            return redirect('index')
        org_ciudad = request.POST.get('orgCiudad')
        org_cpostal = request.POST.get('orgCPostal')
        org_telefono = request.POST.get('orgTelefono')
        ck_org = request.POST.get('ckOrg')
        errores = []
        if ck_org is None:
            errores.append("Tienes que aceptar la política de uso de datos de los asistentes")

        if org_ciudad == '':
            errores.append("Para organizadores, la ciudad es necesaria")
            context['b_ciu'] = "border-danger"
        elif org_ciudad != '':
            context['orgCiudad'] = org_ciudad

        if org_cpostal == '':
            errores.append("Para organizadores, el código postal es necesario")
            context['b_cp'] = "border-danger"
        elif org_ciudad != '':
            context['orgCPostal'] = org_ciudad

        if org_telefono == '':
            errores.append("Para organizadores, el teléfono es necesario")
            context['b_tel'] = "border-danger"
        elif org_telefono != '':
            context['orgTelefono'] = org_telefono

        if request.POST.get('orgDireccion') == '':
            errores.append("La dirección no puede estar vacía")
        else:
            context['orgDireccion'] = request.POST.get('orgDireccion')

        if len(errores) == 0:
            org = Organizador(nickname=request.user.username, id=request.user.id,
                              direccion=request.POST.get('orgDireccion'), exclusive_org=False, ciudad=org_ciudad,
                              cpostal=org_cpostal, telefono=org_telefono)
            org.save()
            request.session['profile'] = 'org'
            context['errores'] = None
            context['errores'] = "La dirección no puede estar vacía"
        else:
            context['errores'] = errores
            return render(request, "freeketapp/registro_organizador.html", context)
        return redirect('index')
    return render(request, "freeketapp/registro_organizador.html", context)


@login_required(login_url='/login')
def organizador(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

    return render(request, "freeketapp/organizador.html", context)


def resultados(request):
    context = {}
    if request.user.is_authenticated:
        context['name'] = request.user.username
        context['islogged'] = 'y'
        context['profile'] = request.session['profile']
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True
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


@login_required(login_url='/login')
def reader(request, id_evento):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
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
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True
    try:
        ev = Evento.objects.get(url_id=id_evento)
        if ev.organizador.id != request.user.id:
            raise Http404("El evento no existe")
        context['url'] = ev.url_id
    except:
        raise Http404("El evento no existe!")

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


def mail_lista_espera(l_espera):
    for i in l_espera:
        email_dir = i.usuario.email
        message = "Hola, " + i.usuario.username + "\nTe escribimos para hacerte saber que hay nuevas entradas disponibles para el evento \"" + i.evento.titulo + "\""
        message += ", para el cual te apuntaste a la lista de espera. No dudes en asistir pero... tienes que ser rápido, ya que el número de entradas es limitado"
        message += " y puede que no seas la única persona en recibir este email...\n"
        message += "\nAcceso al evento: freeket.es/evento/" + i.evento.url_id
        email = EmailMessage(
            'Nuevas entradas disponibles!', message, 'freeketmail@gmail.com', [email_dir])
        email.send()


def mail_devolver(entrada, evento):
    email_dir = entrada.usuario.email
    message = "Hola, " + entrada.usuario.username + "\nTe escribimos para confirmar la devolución de tu entrada para el evento \"" + entrada.evento.titulo + "\""
    message += "\nLamentamos que no puedas asistir al evento y agradecemos profundamente el tiempo que has dedicado a devolver tu entrada."
    email = EmailMessage(
        'Freeket: devolución de entrada', message, 'freeketmail@gmail.com', [email_dir])
    email.send()

    entrada.delete()
    evento.numero_entradas_actual += 1
    evento.save()


@login_required(login_url='/login')
def devolver(request, id_entrada):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

    try:
        id_entrada = uuid.UUID(id_entrada).hex

        entrada = Entrada.objects.filter(id=id_entrada)

        if entrada.count == 0:
            raise Http404()
        else:
            entrada = entrada[0]
            if request.user.id != entrada.usuario.id:
                raise Http404()
            evento = entrada.evento
            # Mandamos email
            t_dev = threading.Thread(target=mail_devolver, args=(entrada, evento), kwargs={})
            t_dev.setDaemon(True)
            t_dev.start()

            context['devolver'] = True
            entradas = Entrada.objects.filter(usuario=request.user)
            ids = []
            evs = []
            fechas = []
            for i in entradas:
                ids.append(i)
                evs.append(i.evento)
                fechas.append(i.fecha_adquisicion.strftime("%d-%m-%Y"))

            evs.reverse()
            ids.reverse()
            fechas.reverse()
            context['elementos'] = zip(ids, evs, fechas)
            # LISTA DE ESPERA - COMPROBAR Y AVISAR
            l_espera = ListaEspera.objects.filter(evento=evento)
            if l_espera.count() > 0:
                t = threading.Thread(target=mail_lista_espera, args=(l_espera,), kwargs={})
                t.setDaemon(True)
                t.start()

    except:
        raise Http404()

    return render(request, "freeketapp/misentradas.html", context)


@login_required(login_url='/login')
def lista_espera(request):
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

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
    context = {'islogged': 'y', 'name': request.user.username, 'profile': request.session['profile']}
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() == 0:
        context['org'] = False
        return redirect('index')
    else:
        context['org'] = True
        if org[0].exclusive_org:
            context['assist'] = False
        else:
            context['assist'] = True

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


def error_404_view(request, exception):
    context = {}
    if request.user.is_authenticated:
        context['name'] = request.user.username
        context['islogged'] = 'y'
        context['profile'] = request.session['profile']
        org = Organizador.objects.filter(id=request.user.id)
        if org.count() == 0:
            context['org'] = False
        else:
            context['org'] = True
            if org[0].exclusive_org:
                context['assist'] = False
            else:
                context['assist'] = True
    else:
        context['islogged'] = 'n'

    return render(request, 'freeketapp/404.html', context)
