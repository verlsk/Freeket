import json
import os
import threading
from datetime import timedelta, date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, redirect

from freeketapp.models import Organizador, Evento, Entrada
from freeketapp.views import get_context, validate_date, isTimeFormat, RepresentsInt, enviar_email_cambios, \
    enviar_email_informativo, enviar_email_invitaciones, enviar_email_cancelar


@login_required(login_url='/login')
def gestionar_eventos(request):
    context = get_context(request)
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
    context = get_context(request)
    context['e_active'] = "btnSideActive"
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


@login_required(login_url='/login')
def gestionar_eventos_modificar(request, id_evento):
    context = get_context(request)
    context['id_evento'] = id_evento
    context['m_active'] = "btnSideActive"
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


@login_required(login_url='/login')
def gestionar_eventos_notificacion(request, id_evento):
    context = get_context(request)
    context['id_evento'] = id_evento
    context['n_active'] = "btnSideActive"
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
    context = get_context(request)
    context['id_evento'] = id_evento
    context['i_active'] = "btnSideActive"
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


@login_required(login_url='/login')
def gestionar_eventos_cancelar(request, id_evento):
    org = Organizador.objects.filter(id=request.user.id)
    try:
        evento = Evento.objects.get(url_id=id_evento)
        # comprobar propietario del evento
        if evento.organizador.nickname != request.user.username:
            raise Http404("El evento no existe")
        context = get_context(request)
        context['id_evento'] = id_evento
        context['c_active'] = "btnSideActive"
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
    context = get_context(request)
    context['id_evento'] = id_evento
    context['l_active'] = "btnSideActive"

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