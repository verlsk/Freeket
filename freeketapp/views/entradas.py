import locale
import os
import threading
import uuid

from cryptography.fernet import Fernet
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas

from freeketapp.models import Entrada, ListaEspera
from freeketapp.views import get_context


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
    titulo_3 = ""
    font_size = (700//len(entrada.evento.titulo))*2


    if font_size > 22:
        font_size = 32

    index_cut = 570 // font_size
    cut = 0
    if len(entrada.evento.titulo) > 32:
        for i in entrada.evento.titulo[index_cut:]:
            if i == ' ':
                break
            cut += 1

        titulo_1 = entrada.evento.titulo[:index_cut + cut]
        titulo_2 = entrada.evento.titulo[index_cut + cut + 1:]
    else:
        titulo_1 = entrada.evento.titulo
    text = p.beginText(x_margin, 770)
    text.setFont("Times-Roman", font_size)
    text.textLine(titulo_1)
    text.textLine(titulo_2)
    text.setFont("Times-Roman", 22)
    text.textLine("")
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
    context = get_context(request)
    if context['profile'] == 'org':
        return redirect('organizador')

    ids = []
    evs = []
    fechas = []

    entradas = Entrada.objects.filter(usuario=request.user)
    for i in entradas:
        ids.append(i)
        evs.append(i.evento)
        fechas.append(i.fecha_adquisicion.strftime("%d-%m-%Y"))

    evs.reverse()
    ids.reverse()
    fechas.reverse()
    context['ids'] = ids
    context['elementos'] = zip(ids, evs, fechas)

    if entradas.count() > 0:
        context['hayentradas'] = True
    else:
        context['hayentradas'] = False
    return render(request, "freeketapp/misentradas.html", context)
