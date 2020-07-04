import os
import threading
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

from freeketapp.views import get_context
from freeketapp.views.entradas import get_entrada
from freeketapp.models import *


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


def send_confirmation_email(user):
    confirmation_code = ConfirmationCode.objects.get(usuario=user)
    title = "Freeket: Confirmación de email"
    content = "Bienvenido a Freeket, " + user.username + "!\n\n"
    content += "Para confimar tu email y poder adquirir entradas, accede a la siguiente página: "
    content += "http://freeket.es/confirmation/" + str(confirmation_code.id) + "/" + user.username
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


def send_forgot_password_email(user, password):
    title = "Freeket: Reestablecimiento de contraseña"
    content = "Tus nuevos credenciales son: \nUsuario: " + user.username + "\nContraseña: " + password
    content += "\nInicia sesión y accede a \"Mi perfil\" para modificarla."
    send_mail(title, content, 'freeketmail@gmail.com', [user.email], fail_silently=False)


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
    context = get_context(request)
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