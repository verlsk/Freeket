import uuid

from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch

from freeketapp.models import Organizador, ConfirmationCode
from freeketapp.views.auth_profile_check import get_context
from freeketapp.views.email_tasks import send_confirmation_email, send_forgot_password_email

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
            # no lo necesitamos mas
            id_confirmacion.delete()
            context['texto'] = "Email confirmado correctamente!"
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
        raise Http404()
    return render(request, "freeketapp/confirmacion.html", context)



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
def cerrar_sesion(request):
    context = {}
    logout(request)
    return redirect('index')