import uuid

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from freeketapp.models import ConfirmationCode, Organizador
from freeketapp.views import get_context, send_confirmation_email


@login_required(login_url='/login')
def mi_perfil(request):
    context = get_context(request)
    context['m_active'] = "btnSideActive"
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
                    prev_conf = ConfirmationCode.objects.filter(usuario=request.user)
                    if prev_conf.count() == 1:
                        prev_conf[0].delete()
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
    org = Organizador.objects.filter(id=request.user.id)
    if org.count() > 0:
        org = org[0]
        context['orgDireccion'] = org.direccion
        context['orgCiudad'] = org.ciudad
        context['orgCPostal'] = org.cpostal
        context['orgTelefono'] = org.telefono

    return render(request, "freeketapp/mi_perfil.html", context)


@login_required(login_url='/login')
def confirmar_email(request):
    context = get_context(request)
    context['c_active'] = "btnSideActive"
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
def reset_password(request):
    context = get_context(request)
    context['r_active'] = "btnSideActive"
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

@login_required(login_url='/login')
def registro_asistente(request):
    context = get_context(request)
    context['a_active'] = "btnSideActive"

    org = Organizador.objects.filter(id=request.user.id)
    if org.count() > 0:
        org = org[0]
    else:
        return redirect('index')
    if request.method == 'POST':
        org.exclusive_org = False
        org.save()
        request.session['profile'] = 'assist'
        return redirect('index')

    return render(request, "freeketapp/registro_asistente.html", context)


@login_required(login_url='/login')
def registro_organizador(request):
    context = get_context(request)
    context['o_active'] = "btnSideActive"

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
