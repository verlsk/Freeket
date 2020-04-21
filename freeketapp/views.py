from datetime import datetime
from io import BytesIO
import time
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render, redirect

from django.http import HttpResponse, Http404, HttpResponseForbidden
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


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['islogged'] = 'y'
        context['name'] = request.user.username
    else:
        context['islogged'] = 'n'
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
        time.strptime(input, '%H:%M')
        if len(input.split(":")[0]) > 2 or len(input.split(":")[1]) != 2:
            return False
        else:
            return True
    except ValueError:
        return False


@login_required(login_url='/login')
def crear_evento(request):
    context = {'islogged': 'y', 'name': request.user.username}
    errores = []
    if request.method == 'POST':
        try:
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
            fecha = validate_date(fecha)
            if not fecha:
                errores.append("Formato de fecha incorrecto")

            hora = request.POST.get('horaEvento', '')

            if not isTimeFormat(hora):
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

            if titulo == '' or nentradas == '' or ciudad == '' or direccion == '' or cpostal == '' or not RepresentsInt(
                    nentradas) or int(nmaxentradas) < 0 or int(nmaxentradas) > 10 or int(nentradas) < 0:
                errores.append("Campos obligatorios vacíos o erróneos")
            context['errores'] = errores
            if len(errores) == 0:
                context['publicado'] = True
                # generamos clave para desencriptar entradas de evento
                key = Fernet.generate_key().decode()
                # uuid para evento
                id_evento = uuid.uuid4()
                # usuario que organiza el evento
                e = Evento(id=id_evento, titulo=titulo, url_id=url_id, fecha=fecha, hora=hora,
                           numero_entradas_inicial=nentradas,
                           max_entradas_user=nmaxentradas, numero_entradas_actual=nentradas,
                           organizador=org, key=key, ciudad=ciudad, direccion=direccion, cpostal=cpostal)
                e.save()
        except:
            errores.append("Campos obligatorisos vacíos o erróneos")
            context['errores'] = errores

    return render(request, "freeketapp/plantilla_eventos.html", context)


def pagina_evento(request, id_evento):
    context = {}
    if request.user.is_authenticated:
        context['name'] = request.user.username
        context['islogged'] = 'y'
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
            if request.user.id == evento.organizador.id:
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
                    enviar_entrada(entrada)
                # actualizacion del numero de entradas
                e.numero_entradas_actual -= nentradas
                context['adquiridas'] = 'y'
            context['errores'] = errores

        if evento is None:
            raise Http404("El evento no existe!")
        else:
            titulo_aux = evento.titulo
            context['titulo'] = titulo_aux
            # hay que actualizarlo cuando el usuario esté logeado, restanlo al max_entradas_user si ya ha comprado
            # entradas antes
            context['nmax'] = evento.max_entradas_user
            eng_date_format = evento.fecha
            if eng_date_format < date.today():
                context['mostrarcomprar'] = 'n'
            else:
                context['mostrarcomprar'] = 'y'

            esp_date_format = eng_date_format.strftime("%d de %B de %Y")
            context['fecha'] = esp_date_format
            context['hora'] = evento.hora
            context['url_id'] = id_evento
            context['ciudad'] = evento.ciudad
            context['direccion'] = evento.direccion
            context['cpostal'] = evento.cpostal
    except Evento.DoesNotExist:
        raise Http404("El evento no existe!")
    except ValueError:
        raise Http404("El evento no existe!")

    return render(request, "freeketapp/pagina_evento.html", context)


# Generacion de PDF con entrada
def get_entrada(entrada, p):
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

    text = p.beginText(40, 750)
    text.setFont("Times-Roman", 14)
    text.textLine("Aqui tienes tu entrada para: ")
    text.textLine()
    text.setFont("Times-Roman", 28)
    text.textLine(entrada.evento.titulo)

    p.drawText(text)

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
    titulos = []
    context = {}
    # usuario = Usuario.objects.get(id=1)
    entradas = Entrada.objects.filter(usuario=request.user)
    for i in entradas:
        ids.append(str(i.id))
        titulos.append(i.evento.titulo)

    context['islogged'] = 'y'
    context['name'] = request.user.username
    context['ids'] = ids
    context['titulos'] = titulos
    context['elementos'] = zip(ids, titulos)
    return render(request, "freeketapp/misentradas.html", context)


def registro(request):
    context = {'showform': True}
    errores = []
    context['errores'] = errores
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':

        username = request.POST.get('username').lower()
        name = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        rep_password = request.POST.get('repPassword')
        duplicate_users = User.objects.filter(username=username)
        duplicated_email = User.objects.filter(email=email)
        if duplicate_users.exists():
            errores.append("Nombre de usuario existente")
        if duplicated_email.exists():
            errores.append("Email registrado por otro usuario")
        if password != rep_password:
            errores.append("Las contraseñas no coinciden")
        if len(password) < 8:
            errores.append("La contraseña es demasiado corta")
        if username == '' or email == '' or password == '':
            errores.append("Campos obligatorios vacíos")
        if len(errores) > 0:
            context['errores'] = errores
        else:
            context['showform'] = False
            context[
                'texto'] = "Te has registrado correctamente. Revisa tu bandeja de correo electrónico, ya que te hemos mandado un email de confirmación. "
            user = User.objects.create_user(username, email, password)
            user.first_name = name
            user.last_name = apellido
            user.save()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

            # mandar correo de confirmacion
            confirmation_code = ConfirmationCode(id=uuid.uuid4(), usuario=user)
            confirmation_code.save()
            send_confirmation_email(user)

    return render(request, "freeketapp/registro.html", context)


def send_confirmation_email(user):
    confirmation_code = ConfirmationCode.objects.get(usuario=user)
    title = "Freeket: Confirmación de email"
    content = "Bienvenido a Freeket, " + user.username + "!\n\n"
    content += "Para confimar tu email y poder adquirir entradas, accede a la siguiente página: "
    content += "127.0.0.1:8000/confirmation/" + str(confirmation_code.id) + "/" + user.username
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


def my_login(request):
    context = {}
    if request.user.is_authenticated:
        logout(request)
    try:
        if request.method == 'POST':
            username = request.POST.get('username').lower()
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
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
    if request.user.is_authenticated:
        context['islogged'] = 'y'
        context['name'] = request.user.username
    else:
        context['islogged'] = 'n'
    try:
        user_object = User.objects.get(username=user)
        id_confirmacion = ConfirmationCode.objects.get(usuario=user_object)
        if str(id_confirmacion.id) == id_confirmacion_url:
            context['texto'] = "Email confirmado correctamente!"
            # no lo necesitamos mas
            id_confirmacion.delete()
        else:
            context['texto'] = "Fallo en la confirmación del email"
    except ValueError:
        raise Http404("Codigo incorrecto")
    return render(request, "freeketapp/confirmacion.html", context)


@login_required(login_url='/login')
def reset_password(request):
    context = {'islogged': 'y', 'name': request.user.username}
    errores = []
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
                login(request, user)
                context['texto'] = "La contraseña se ha actualizado correctamente."
        else:
            errores.append("La contraseña actual proporcionada es incorrecta")
            context['errores'] = errores

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
    context = {'islogged': 'y', 'name': request.user.username}
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

        user = authenticate(request, username=request.user, password=password)

        if user is not None:
            request.user.first_name = name
            request.user.last_name = apellido
            duplicated_email = User.objects.filter(email=email.lower())
            if duplicated_email.count() == 1 and duplicated_email[0] != request.user:
                errores.append("Este email pertenece a otro usuario")
            elif duplicated_email.count() > 1:
                errores.append("Este email pertenece a otro usuario")
            if email == '':
                errores.append("El campo \"Email\" no puede estar vacío")
            else:
                if request.user.email != email.lower():
                    request.user.email = email.lower()
                    request.user.save()
                    context['texto'] = "Datos actualizados correctamente. Te hemos mandado un email de confirmación"
                    # mandar correo de confirmacion
                    confirmation_code = ConfirmationCode(id=uuid.uuid4(), usuario=request.user)
                    confirmation_code.save()
                    send_confirmation_email(request.user)
                else:
                    context['texto'] = "Datos actualizados correctamente."
        else:
            errores.append("Contraseña incorrecta")

    context['errores'] = errores
    context['nombre'] = request.user.first_name
    context['apellido'] = request.user.last_name
    context['email'] = request.user.email

    return render(request, "freeketapp/mi_perfil.html", context)


@login_required(login_url='/login')
def confirmar_email(request):
    context = {'islogged': 'y', 'name': request.user.username}

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
    redirect('index')
    return render(request, "freeketapp/base.html", context)


@login_required(login_url='/login')
def gestionar_eventos(request):
    context = {'islogged': 'y', 'name': request.user.username}
    org = Organizador.objects.filter(nickname=request.user.username)

    if org.count() == 1:
        org = org[0]
        eventos = Evento.objects.filter(organizador=org)
        context['eventos'] = eventos
        context['mostrareventos'] = 'y'
    else:
        context['mostrareventos'] = 'n'
        # no hay eventos que mostrar

    return render(request, "freeketapp/gestionar_eventos.html", context)
