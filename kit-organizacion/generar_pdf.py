"""Genera la agenda digital (PDF con enlaces) de Luisa Figueroa: oct 2026 – dic 2027.

Uso:  python3 generar_pdf.py
Requiere: reportlab y Pillow.
"""
import calendar
import datetime as dt
import io
import os
import random

from PIL import Image, ImageDraw, ImageFilter
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "Agenda-Luisa-Figueroa-2026-2027.pdf")
NOMBRE = "Luisa Figueroa"

for nombre, archivo in [("Script", "GreatVibes-Regular.ttf"), ("Sans", "Montserrat-Regular.ttf"),
                        ("SansSemi", "Montserrat-SemiBold.ttf"), ("SansBold", "Montserrat-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(nombre, os.path.join(AQUI, "fuentes", archivo)))

# Página tipo tablet (proporción 2:3)
W, H = 800, 1200
TAB_X = 738           # inicio de la franja de pestañas
MX = 44               # margen izquierdo
CW = TAB_X - MX - 26  # ancho útil del contenido

TINTA = HexColor("#3f3f46")
GRIS = HexColor("#71717a")
LINEA = HexColor("#c9c9cf")
SUAVE = HexColor("#eeeef1")
ACENTO = HexColor("#c0485a")   # rojo suave de los checks del video
TAB = HexColor("#4b4b52")
TAB_ON = HexColor("#c0485a")

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ABREV = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
DIAS = ["DOMINGO", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
DIAS_TIT = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
INI = ["D", "L", "M", "M", "J", "V", "S"]

LISTA_MESES = [(2026, m) for m in (10, 11, 12)] + [(2027, m) for m in range(1, 13)]
SECCIONES = [("cal", "Calendario"), ("sem", "Semanas"), ("hab", "Hábitos"),
             ("rut", "Rutinas"), ("pre", "Presupuesto"), ("lim", "Limpieza")]

HABITOS = ["Tomar agua", "Skincare", "Entrenar", "Leer 10 páginas", "Dormir 7–8 h",
           "Comer sano", "Sin redes sociales", "", "", ""]


# ---------------------------------------------------------------- fondo mármol
def fondo_marmol():
    random.seed(7)
    s = 2
    img = Image.new("RGB", (W // s, H // s), (246, 246, 247))
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for _ in range(45):
        x, y = random.randint(-80, W // s), random.randint(-80, H // s)
        r = random.randint(40, 170)
        g = random.randint(200, 228)
        d.ellipse([x, y, x + r * 1.6, y + r], fill=(g, g, g + 3, random.randint(14, 34)))
    capa = capa.filter(ImageFilter.GaussianBlur(28))
    img.paste(capa, (0, 0), capa)
    vetas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(vetas)
    for _ in range(9):
        x, y = random.randint(0, W // s), random.randint(0, H // s)
        pts = []
        for _ in range(28):
            pts.append((x, y))
            x += random.randint(-6, 26)
            y += random.randint(-14, 18)
        d.line(pts, fill=(170, 170, 176, 60), width=1)
    vetas = vetas.filter(ImageFilter.GaussianBlur(1.2))
    img.paste(vetas, (0, 0), vetas)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    buf.seek(0)
    return ImageReader(buf)


FONDO = fondo_marmol()


# ---------------------------------------------------------------- utilidades
def semanas_del_rango():
    """Semanas domingo–sábado; cada una pertenece al mes de su miércoles (limitado al rango)."""
    inicio = dt.date(2026, 10, 1)
    inicio -= dt.timedelta(days=(inicio.weekday() + 1) % 7)
    fin = dt.date(2027, 12, 31)
    semanas = []
    d = inicio
    while d <= fin:
        mitad = d + dt.timedelta(days=3)
        clave = (mitad.year, mitad.month)
        if clave < LISTA_MESES[0]:
            clave = LISTA_MESES[0]
        if clave > LISTA_MESES[-1]:
            clave = LISTA_MESES[-1]
        semanas.append((d, clave))
        d += dt.timedelta(days=7)
    return semanas


SEMANAS = semanas_del_rango()


def semanas_de(mes):
    return [s for s, m in SEMANAS if m == mes]


def semana_de_fecha(fecha):
    for s, _ in SEMANAS:
        if s <= fecha < s + dt.timedelta(days=7):
            return s
    return None


def id_mes(y, m, sec="cal"):
    return f"{sec}-{y}-{m:02d}"


def id_sem(inicio):
    return f"sem-{inicio.isoformat()}"


class Agenda:
    def __init__(self):
        self.c = canvas.Canvas(SALIDA, pagesize=(W, H))
        self.c.setTitle(f"Agenda Digital 2026–2027 · {NOMBRE}")
        self.c.setAuthor(NOMBRE)
        self.c.setSubject("Agenda digital con enlaces para tablet")

    # -- primitivas
    def texto(self, x, y, s, font="Sans", size=10, color=TINTA, align="left"):
        c = self.c
        c.setFont(font, size)
        c.setFillColor(color)
        {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, s)

    def caja(self, x, y, w, h, r=8, fill=None, stroke=LINEA, lw=0.8):
        c = self.c
        c.setLineWidth(lw)
        c.setStrokeColor(stroke or white)
        if fill is not None:
            c.setFillColor(fill)
        c.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1 if fill is not None else 0)

    def check(self, x, y, s=10):
        self.caja(x, y, s, s, r=2, fill=white, stroke=GRIS, lw=0.6)

    def lineas(self, x, y_top, w, h, paso=22):
        c = self.c
        c.setStrokeColor(LINEA)
        c.setLineWidth(0.5)
        y = y_top - paso
        while y > y_top - h + 2:
            c.line(x, y, x + w, y)
            y -= paso

    def link(self, destino, x, y, w, h):
        self.c.linkRect("", destino, (x, y, x + w, y + h), relative=0, thickness=0)

    def titulo(self, s, y=H - 108, size=64, x=MX):
        self.texto(x, y, s, font="Script", size=size)

    def etiqueta(self, x, y, s, size=8.5, color=GRIS, align="left"):
        self.texto(x, y, s.upper(), font="SansSemi", size=size, color=color, align=align)

    # -- página base
    def nueva(self, destino, titulo_marcador=None, nivel=0, activo=None):
        c = self.c
        c.drawImage(FONDO, 0, 0, W, H)
        c.bookmarkPage(destino)
        if titulo_marcador:
            c.addOutlineEntry(titulo_marcador, destino, level=nivel, closed=True)
        self.pestanas(activo)
        self.texto(MX, 26, f"{NOMBRE}  ·  Agenda 2026–2027", size=7.5, color=GRIS)

    def fin(self):
        self.c.showPage()

    def pestanas(self, activo):
        c = self.c
        c.setFillColor(HexColor("#2f2f35"))
        c.rect(TAB_X, 0, W - TAB_X, H, stroke=0, fill=1)
        items = [("INICIO", "indice", "ini"), ("2026", "anio-2026", "a26"), ("2027", "anio-2027", "a27")]
        items += [(f"{ABREV[m - 1]} {str(y)[2:]}", id_mes(y, m), (y, m)) for y, m in LISTA_MESES]
        top, alto = H - 14, (H - 28) / len(items)
        for i, (txt, dest, clave) in enumerate(items):
            y0 = top - (i + 1) * alto
            on = clave == activo
            c.setFillColor(TAB_ON if on else TAB)
            c.roundRect(TAB_X + 6, y0 + 2, W - TAB_X - 12, alto - 4, 5, stroke=0, fill=1)
            c.saveState()
            c.translate(TAB_X + (W - TAB_X) / 2 + 3, y0 + alto / 2)
            c.rotate(-90)
            c.setFont("SansBold", 9.5)
            c.setFillColor(white)
            c.drawCentredString(0, 0, txt)
            c.restoreState()
            self.link(dest, TAB_X, y0, W - TAB_X, alto)

    def barra_mes(self, y, m, sec):
        """Pastillas de navegación a las secciones del mes (como la barra del video)."""
        x, alto = MX, 26
        ancho = (CW - 5 * 6) / 6
        for clave, nombre in SECCIONES:
            on = clave == sec
            dest = id_sem(semanas_de((y, m))[0]) if clave == "sem" else id_mes(y, m, clave)
            self.caja(x, H - 52, ancho, alto, r=13, fill=TINTA if on else white, stroke=None if on else LINEA)
            self.texto(x + ancho / 2, H - 52 + 9, nombre, font="SansSemi", size=9,
                       color=white if on else TINTA, align="center")
            self.link(dest, x, H - 52, ancho, alto)
            x += ancho + 6

    # ---------------------------------------------------------------- páginas
    def portada(self):
        c = self.c
        c.drawImage(FONDO, 0, 0, W, H)
        c.bookmarkPage("portada")
        c.addOutlineEntry("Portada", "portada")
        self.caja(90, 330, W - 180, 560, r=24, fill=Color(1, 1, 1, 0.75), stroke=LINEA)
        self.texto(W / 2, 760, "Agenda", font="Script", size=110, align="center")
        self.texto(W / 2, 680, "Digital", font="Script", size=84, align="center")
        self.etiqueta(W / 2, 610, "Octubre 2026 — Diciembre 2027", size=13, color=TINTA, align="center")
        c.setStrokeColor(ACENTO)
        c.setLineWidth(1.2)
        c.line(W / 2 - 60, 585, W / 2 + 60, 585)
        self.texto(W / 2, 500, NOMBRE, font="Script", size=58, align="center", color=ACENTO)
        self.etiqueta(W / 2, 440, "Calendario · Semanas · Hábitos · Rutinas", size=9, align="center")
        self.etiqueta(W / 2, 422, "Presupuesto · Limpieza", size=9, align="center")
        self.caja(W / 2 - 80, 360, 160, 34, r=17, fill=TINTA, stroke=None)
        self.texto(W / 2, 372, "ABRIR AGENDA", font="SansBold", size=10, color=white, align="center")
        self.link("indice", W / 2 - 80, 360, 160, 34)
        self.fin()

    def indice(self):
        self.nueva("indice", "Índice", activo="ini")
        self.titulo("Mi organización")
        self.etiqueta(MX + 4, H - 140, f"Agenda de {NOMBRE}", size=10, color=ACENTO)
        y = H - 200
        self.etiqueta(MX, y, "Vista anual")
        for i, (txt, dest) in enumerate([("Año 2026", "anio-2026"), ("Año 2027", "anio-2027")]):
            x = MX + i * (CW / 2 + 5)
            self.caja(x, y - 66, CW / 2 - 5, 50, r=12, fill=white)
            self.texto(x + 20, y - 50, txt, font="Script", size=30)
            self.link(dest, x, y - 66, CW / 2 - 5, 50)
        y -= 110
        self.etiqueta(MX, y, "Meses")
        cols, bw, bh = 3, (CW - 20) / 3, 74
        for i, (yy, m) in enumerate(LISTA_MESES):
            x = MX + (i % cols) * (bw + 10)
            yb = y - 18 - (i // cols + 1) * (bh + 10) + 10
            self.caja(x, yb, bw, bh, r=12, fill=white)
            self.texto(x + 16, yb + 34, MESES[m - 1], font="Script", size=30)
            self.etiqueta(x + bw - 14, yb + 12, str(yy), color=ACENTO, align="right")
            self.link(id_mes(yy, m), x, yb, bw, bh)
        yb -= 50
        self.etiqueta(MX, yb, "Cómo usar")
        notas = ["Toca las pestañas laterales para saltar a cualquier mes.",
                 "En cada mes, la barra superior te lleva a Semanas, Hábitos, Rutinas,",
                 "Presupuesto y Limpieza. Toca un día del calendario para abrir su semana.",
                 "Ábrela en GoodNotes, Samsung Notes, Noteshelf o Xodo y escribe con el lápiz."]
        for i, n in enumerate(notas):
            self.texto(MX, yb - 22 - i * 16, n, size=10, color=GRIS)
        self.fin()

    def mini_mes(self, x, y_top, w, y, m):
        self.texto(x, y_top - 26, MESES[m - 1], font="Script", size=28)
        cw = w / 7
        for i, l in enumerate(INI):
            self.texto(x + cw * i + cw / 2, y_top - 46, l, font="SansBold", size=7.5, color=GRIS, align="center")
        primero = (dt.date(y, m, 1).weekday() + 1) % 7
        for d in range(1, calendar.monthrange(y, m)[1] + 1):
            pos = primero + d - 1
            cx = x + cw * (pos % 7) + cw / 2
            cy = y_top - 62 - (pos // 7) * 14
            self.texto(cx, cy, str(d), size=7.5, align="center")
        self.link(id_mes(y, m), x, y_top - 150, w, 150)

    def anual(self, anio):
        meses = [ym for ym in LISTA_MESES if ym[0] == anio]
        self.nueva(f"anio-{anio}", f"Año {anio}", activo="a26" if anio == 2026 else "a27")
        self.titulo(f"Año {anio}")
        self.etiqueta(MX + 4, H - 140, "Toca un mes para abrirlo", color=GRIS)
        cols = 3
        bw = (CW - 20) / cols
        bh = 236 if anio == 2027 else 300
        for i, (y, m) in enumerate(meses):
            x = MX + (i % cols) * (bw + 10)
            yt = H - 160 - (i // cols) * (bh + 10)
            self.caja(x, yt - bh, bw, bh, r=12, fill=Color(1, 1, 1, 0.8))
            self.mini_mes(x + 12, yt, bw - 24, y, m)
            self.lineas(x + 12, yt - 152, bw - 24, bh - 156, paso=18)
        if anio == 2026:
            yt = H - 160 - bh - 30
            self.etiqueta(MX, yt, "Metas para lo que queda del año")
            self.caja(MX, 70, CW, yt - 84, r=12, fill=Color(1, 1, 1, 0.8))
            self.lineas(MX + 16, yt - 14, CW - 32, yt - 100, paso=26)
        self.fin()

    def calendario(self, y, m):
        self.nueva(id_mes(y, m), f"{MESES[m - 1]} {y}", activo=(y, m))
        self.barra_mes(y, m, "cal")
        self.titulo(MESES[m - 1], y=H - 128, size=70)
        self.etiqueta(MX + 6, H - 156, str(y), size=12, color=ACENTO)
        top = H - 176
        cw = CW / 7
        for i, d in enumerate(DIAS):
            self.texto(MX + cw * i + cw / 2, top - 4, d, font="SansSemi", size=7.5, color=GRIS, align="center")
        primero = (dt.date(y, m, 1).weekday() + 1) % 7
        ndias = calendar.monthrange(y, m)[1]
        filas = (primero + ndias + 6) // 7
        ch = 640 / filas
        y0 = top - 16
        for pos in range(filas * 7):
            cx = MX + cw * (pos % 7)
            cy = y0 - (pos // 7 + 1) * ch
            d = pos - primero + 1
            dentro = 1 <= d <= ndias
            self.caja(cx + 2, cy + 2, cw - 4, ch - 4, r=6,
                      fill=Color(1, 1, 1, 0.85) if dentro else Color(1, 1, 1, 0.3), stroke=LINEA)
            if dentro:
                self.texto(cx + 9, cy + ch - 18, str(d), font="SansSemi", size=10)
                sem = semana_de_fecha(dt.date(y, m, d))
                if sem:
                    self.link(id_sem(sem), cx + 2, cy + 2, cw - 4, ch - 4)
        yb = y0 - filas * ch - 18
        self.etiqueta(MX, yb, "Prioridades del mes")
        self.etiqueta(MX + CW / 2 + 8, yb, "Notas")
        for i in range(2):
            x = MX + i * (CW / 2 + 8)
            self.caja(x, 48, CW / 2 - 8, yb - 60, r=10, fill=Color(1, 1, 1, 0.8))
            if i == 0:
                for k in range(int((yb - 80) // 24)):
                    self.check(x + 12, yb - 34 - k * 24)
                    self.c.setStrokeColor(LINEA)
                    self.c.line(x + 30, yb - 34 - k * 24, x + CW / 2 - 22, yb - 34 - k * 24)
            else:
                self.lineas(x + 12, yb - 12, CW / 2 - 32, yb - 70, paso=24)
        self.fin()

    def semana(self, inicio, y, m):
        fin = inicio + dt.timedelta(days=6)
        lista = semanas_de((y, m))
        n = lista.index(inicio) + 1
        self.nueva(id_sem(inicio), activo=(y, m))
        self.barra_mes(y, m, "sem")
        self.titulo(f"Semana {n}", y=H - 116, size=56)
        rango = f"{inicio.day} {ABREV[inicio.month - 1]} – {fin.day} {ABREV[fin.month - 1]} {fin.year}"
        self.etiqueta(MX + 6, H - 140, rango, size=10, color=ACENTO)
        # selector de semanas: SEM 1 2 3 4 5
        x = MX + CW - len(lista) * 30 - 40
        self.etiqueta(x, H - 104, "SEM:", size=9, color=TINTA)
        for i, s in enumerate(lista):
            cx = x + 52 + i * 30
            on = s == inicio
            self.c.setFillColor(TINTA if on else white)
            self.c.setStrokeColor(LINEA)
            self.c.circle(cx, H - 101, 11, stroke=0 if on else 1, fill=1)
            self.texto(cx, H - 104.5, str(i + 1), font="SansBold", size=9,
                       color=white if on else TINTA, align="center")
            self.link(id_sem(s), cx - 11, H - 112, 22, 22)
        # 7 días + panel lateral
        top = H - 160
        izq = CW * 0.64
        bh = (top - 52 - 6 * 8) / 7
        for i in range(7):
            d = inicio + dt.timedelta(days=i)
            by = top - (i + 1) * bh - i * 8
            self.caja(MX, by, izq, bh, r=10, fill=Color(1, 1, 1, 0.85))
            self.texto(MX + 14, by + bh - 22, DIAS_TIT[i], font="Script", size=24)
            self.etiqueta(MX + izq - 14, by + bh - 18, f"{d.day} {ABREV[d.month - 1]}", color=ACENTO, align="right")
            self.lineas(MX + 14, by + bh - 28, izq - 28, bh - 30, paso=20)
        px, pw = MX + izq + 10, CW - izq - 10
        bloques = [("Prioridades", 190), ("Hábitos de la semana", 250), ("Rutina mañana / noche", 180),
                   ("Pendientes", top - 52 - 190 - 250 - 180 - 30)]
        yb = top
        for nombre, alto in bloques:
            self.caja(px, yb - alto, pw, alto, r=10, fill=Color(1, 1, 1, 0.85))
            self.etiqueta(px + 12, yb - 20, nombre, color=TINTA)
            if nombre == "Hábitos de la semana":
                cw = (pw - 96) / 7
                for k, l in enumerate(INI):
                    self.texto(px + 90 + cw * k + cw / 2, yb - 42, l, font="SansBold", size=7.5,
                               color=GRIS, align="center")
                for r, h in enumerate(["Agua", "Ejercicio", "Lectura", "Skincare", "Dormir bien",
                                       "Comer sano", "Sin redes", "", ""]):
                    yy = yb - 62 - r * 20
                    self.texto(px + 12, yy, h, size=8)
                    for k in range(7):
                        self.check(px + 90 + cw * k + cw / 2 - 5, yy - 2, 9)
            elif nombre == "Rutina mañana / noche":
                for col, t in enumerate(["Mañana", "Noche"]):
                    xx = px + 12 + col * (pw / 2)
                    self.texto(xx, yb - 42, t, font="SansSemi", size=8.5, color=ACENTO)
                    for k in range(6):
                        self.check(xx, yb - 62 - k * 18, 8)
                        self.c.setStrokeColor(LINEA)
                        self.c.line(xx + 12, yb - 62 - k * 18, xx + pw / 2 - 24, yb - 62 - k * 18)
            else:
                for k in range(int((alto - 40) // 22)):
                    yy = yb - 44 - k * 22
                    self.check(px + 12, yy, 9)
                    self.c.setStrokeColor(LINEA)
                    self.c.line(px + 28, yy, px + pw - 12, yy)
            yb -= alto + 10
        self.fin()

    def habitos(self, y, m):
        self.nueva(id_mes(y, m, "hab"), activo=(y, m))
        self.barra_mes(y, m, "hab")
        self.titulo("Chequeo de Hábitos", y=H - 116, size=54)
        self.etiqueta(MX + 6, H - 142, f"{MESES[m - 1]} {y}", size=10, color=ACENTO)
        ndias = calendar.monthrange(y, m)[1]
        top, nomw = H - 176, 128
        cw = (CW - nomw) / ndias
        self.caja(MX, top - 30 - len(HABITOS) * 34 - 10, CW, 30 + len(HABITOS) * 34 + 20, r=12,
                  fill=Color(1, 1, 1, 0.85))
        self.etiqueta(MX + 12, top - 16, "Hábito", color=TINTA)
        for d in range(1, ndias + 1):
            cx = MX + nomw + cw * (d - 1) + cw / 2
            dow = (dt.date(y, m, d).weekday() + 1) % 7
            self.texto(cx, top - 10, INI[dow], font="SansBold", size=6.5, color=GRIS, align="center")
            self.texto(cx, top - 21, str(d), font="SansSemi", size=7, align="center")
        for r, h in enumerate(HABITOS):
            yy = top - 52 - r * 34
            if h:
                self.texto(MX + 12, yy + 2, h, size=9)
            else:
                self.c.setStrokeColor(LINEA)
                self.c.line(MX + 12, yy, MX + nomw - 8, yy)
            for d in range(ndias):
                self.check(MX + nomw + cw * d + cw / 2 - 5, yy - 2, 10)
        # progreso semanal
        yb = top - 30 - len(HABITOS) * 34 - 40
        self.etiqueta(MX, yb, "Progreso semanal")
        lista = semanas_de((y, m))
        bw = (CW - (len(lista) - 1) * 10) / len(lista)
        for i, s in enumerate(lista):
            x = MX + i * (bw + 10)
            self.caja(x, yb - 130, bw, 116, r=10, fill=Color(1, 1, 1, 0.85))
            self.texto(x + bw / 2, yb - 40, f"Semana {i + 1}", font="Script", size=24, align="center")
            self.etiqueta(x + bw / 2, yb - 58, f"{s.day} {ABREV[s.month - 1]}", size=7, align="center")
            self.caja(x + 14, yb - 86, bw - 28, 12, r=6, fill=SUAVE, stroke=None)
            self.etiqueta(x + bw / 2, yb - 116, "____ %", size=9, color=TINTA, align="center")
            self.link(id_sem(s), x, yb - 130, bw, 116)
        yb -= 160
        self.etiqueta(MX, yb, "Reflexión del mes")
        self.caja(MX, 48, CW, yb - 60, r=10, fill=Color(1, 1, 1, 0.85))
        self.lineas(MX + 14, yb - 12, CW - 28, yb - 70, paso=24)
        self.fin()

    def rutinas(self, y, m):
        self.nueva(id_mes(y, m, "rut"), activo=(y, m))
        self.barra_mes(y, m, "rut")
        self.titulo("Mis Rutinas", y=H - 116, size=58)
        self.etiqueta(MX + 6, H - 142, f"{MESES[m - 1]} {y}", size=10, color=ACENTO)
        bloques = [("Mañana", ["Tender la cama", "Tomar agua", "Skincare", "Desayunar", "Revisar agenda", "", ""]),
                   ("Tarde", ["Almorzar", "Pausa activa", "Revisar pendientes", "Entrenar", "", "", ""]),
                   ("Noche", ["Preparar ropa", "Skincare", "Leer 10 páginas", "Sin pantallas", "Dormir 7–8 h", "", ""])]
        top = H - 170
        alto = (top - 52 - 20) / 3
        cw = 30
        for i, (nom, items) in enumerate(bloques):
            yt = top - i * (alto + 10)
            self.caja(MX, yt - alto, CW, alto, r=12, fill=Color(1, 1, 1, 0.85))
            self.texto(MX + 16, yt - 38, nom, font="Script", size=36)
            x0 = MX + CW - 7 * cw - 16
            for k, l in enumerate(INI):
                self.texto(x0 + cw * k + cw / 2, yt - 30, l, font="SansBold", size=8, color=GRIS, align="center")
            for r, it in enumerate(items):
                yy = yt - 70 - r * 34
                if it:
                    self.texto(MX + 22, yy + 1, it, size=10)
                else:
                    self.c.setStrokeColor(LINEA)
                    self.c.line(MX + 22, yy, x0 - 20, yy)
                for k in range(7):
                    self.check(x0 + cw * k + cw / 2 - 6, yy - 2, 12)
        self.fin()

    def presupuesto(self, y, m):
        self.nueva(id_mes(y, m, "pre"), activo=(y, m))
        self.barra_mes(y, m, "pre")
        self.titulo("Presupuesto mensual", y=H - 116, size=54)
        self.etiqueta(MX + CW, H - 104, "Mes", align="right")
        self.texto(MX + CW, H - 128, MESES[m - 1], font="Script", size=30, align="right", color=ACENTO)
        y0 = H - 160
        for i, t in enumerate(["Balance inicial", "Balance final"]):
            self.etiqueta(MX + 6, y0 - i * 22, t, color=TINTA)
            self.c.setStrokeColor(LINEA)
            self.c.line(MX + 130, y0 - i * 22 - 2, MX + 330, y0 - i * 22 - 2)

        def tabla(nombre, ytop, filas, con_check):
            self.caja(MX, ytop - 24, 120, 22, r=11, fill=TINTA, stroke=None)
            self.texto(MX + 60, ytop - 16, nombre.upper(), font="SansBold", size=9, color=white, align="center")
            cols = ([("", 26)] if con_check else []) + [("Fecha", 80), ("Descripción", None), ("Valor", 130)]
            fijo = sum(w for _, w in cols if w)
            anchos = [w if w else CW - fijo for _, w in cols]
            yy = ytop - 34
            self.caja(MX, yy - 22, CW, 22, r=4, fill=SUAVE, stroke=None)
            x = MX
            for (t, _), w in zip(cols, anchos):
                self.etiqueta(x + w / 2, yy - 15, t, size=7.5, align="center")
                x += w
            yy -= 22
            self.c.setStrokeColor(LINEA)
            for r in range(filas):
                ry = yy - (r + 1) * 24
                self.c.line(MX, ry, MX + CW, ry)
                if con_check:
                    self.check(MX + 8, ry + 7, 10)
            x = MX
            for w in anchos[:-1]:
                x += w
                self.c.line(x, yy, x, yy - filas * 24)
            yt = yy - filas * 24 - 18
            self.etiqueta(MX + CW - 140, yt, "Total", color=TINTA, align="right")
            self.c.line(MX + CW - 130, yt - 2, MX + CW, yt - 2)
            return yt - 26

        yy = tabla("Entradas", y0 - 56, 8, False)
        yy = tabla("Gastos", yy, 16, True)
        self.caja(MX, yy - 24, 120, 22, r=11, fill=ACENTO, stroke=None)
        self.texto(MX + 60, yy - 16, "TOTALES", font="SansBold", size=9, color=white, align="center")
        tot = ["Total ingresos", "Total gastos", "Balance final", "Diferencia"]
        bw = (CW - 30) / 4
        for i, t in enumerate(tot):
            x = MX + i * (bw + 10)
            self.caja(x, 48, bw, yy - 34 - 48, r=10, fill=Color(1, 1, 1, 0.85))
            self.etiqueta(x + bw / 2, yy - 52, t, size=7.5, align="center")
        self.fin()

    def limpieza(self, y, m):
        self.nueva(id_mes(y, m, "lim"), activo=(y, m))
        self.barra_mes(y, m, "lim")
        self.titulo("Check list de Limpieza", y=H - 116, size=52)
        self.etiqueta(MX + 6, H - 142, f"{MESES[m - 1]} {y}", size=10, color=ACENTO)
        nsem = len(semanas_de((y, m)))
        secciones = [("Diario", INI, ["Tender camas", "Lavar platos", "Barrer", "Limpiar cocina",
                                      "Sacar basura", "Recoger desorden", ""]),
                     ("Semanal", [f"S{i + 1}" for i in range(nsem)],
                      ["Cambiar sábanas", "Limpiar baños", "Trapear pisos", "Lavar ropa", "Sacudir muebles",
                       "Aspirar", ""]),
                     ("Mensual", ["OK"], ["Limpiar nevera", "Limpiar horno", "Lavar cortinas", "Limpiar ventanas",
                                         "Organizar closet", "Lavar cojines", ""])]
        top = H - 170
        alto = (top - 52 - 20) / 3
        for i, (nom, cols, items) in enumerate(secciones):
            yt = top - i * (alto + 10)
            self.caja(MX, yt - alto, CW, alto, r=12, fill=Color(1, 1, 1, 0.85))
            self.texto(MX + 16, yt - 38, nom, font="Script", size=34)
            cw = 30
            x0 = MX + CW - len(cols) * cw - 16
            for k, l in enumerate(cols):
                self.texto(x0 + cw * k + cw / 2, yt - 30, l, font="SansBold", size=8, color=GRIS, align="center")
            for r, it in enumerate(items):
                yy = yt - 70 - r * 32
                if it:
                    self.texto(MX + 22, yy + 1, it, size=10)
                else:
                    self.c.setStrokeColor(LINEA)
                    self.c.line(MX + 22, yy, x0 - 20, yy)
                for k in range(len(cols)):
                    self.check(x0 + cw * k + cw / 2 - 6, yy - 2, 12)
        self.fin()

    def generar(self):
        self.portada()
        self.indice()
        self.anual(2026)
        self.anual(2027)
        for y, m in LISTA_MESES:
            self.calendario(y, m)
            for s in semanas_de((y, m)):
                self.semana(s, y, m)
            self.habitos(y, m)
            self.rutinas(y, m)
            self.presupuesto(y, m)
            self.limpieza(y, m)
        self.c.save()
        print("PDF generado:", SALIDA)


if __name__ == "__main__":
    Agenda().generar()
