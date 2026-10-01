import json
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
import re


URL = "https://www.cooperativa.cl/noticias/deportes"
BASE = "https://www.cooperativa.cl"


class NoticiasParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.noticias = []
        self.enlace_actual = None
        self.titulo_actual = []
        self.dentro_titulo = False

    def handle_starttag(self, tag, attrs):

        attrs = dict(attrs)

        if tag == "a" and "href" in attrs:

            href = attrs["href"]

            if href.startswith("/noticias/deportes/"):
                self.enlace_actual = urljoin(BASE, href)

        if tag in ("h2", "h3") and self.enlace_actual:

            self.dentro_titulo = True
            self.titulo_actual = []

    def handle_data(self, data):

        if self.dentro_titulo:
            self.titulo_actual.append(data)

    def handle_endtag(self, tag):

        if tag in ("h2", "h3") and self.dentro_titulo:

            titulo = " ".join(
                "".join(self.titulo_actual).split()
            )

            if titulo and self.enlace_actual:

                self.noticias.append({
                    "titulo": titulo,
                    "enlace": self.enlace_actual
                })

            self.titulo_actual = []
            self.dentro_titulo = False

class BioBioParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.noticias = []

        self.dentro_article = False
        self.noticia_actual = None

        self.dentro_titulo = False
        self.dentro_fecha = False

        self.titulo_actual = []
        self.fecha_actual = []

    def handle_starttag(self, tag, attrs):

        attrs = dict(attrs)

        # Comienza una noticia
        if tag == "article" and not self.dentro_article:

            self.dentro_article = True

            self.noticia_actual = {
                "titulo": "",
                "enlace": "",
                "fecha": ""
            }

        if not self.dentro_article:
            return

        # Enlace de la noticia
        if tag == "a" and "href" in attrs:

            href = attrs["href"]

            if href.startswith("https://www.biobiochile.cl/noticias/"):
                self.noticia_actual["enlace"] = href

        # Título
        if tag == "h2" and "class" in attrs:

            if "article-title" in attrs["class"]:

                self.dentro_titulo = True
                self.titulo_actual = []

        # Fecha
        if tag == "div" and "class" in attrs:

            if "article-date-hour" in attrs["class"]:

                self.dentro_fecha = True
                self.fecha_actual = []

    def handle_data(self, data):

        if self.dentro_titulo:
            self.titulo_actual.append(data)

        if self.dentro_fecha:
            self.fecha_actual.append(data)

    def handle_endtag(self, tag):

        # Terminó título
        if tag == "h2" and self.dentro_titulo:

            self.noticia_actual["titulo"] = " ".join(
                "".join(self.titulo_actual).split()
            )

            self.titulo_actual = []
            self.dentro_titulo = False

        # Terminó fecha
        if tag == "div" and self.dentro_fecha:

            self.noticia_actual["fecha"] = " ".join(
                "".join(self.fecha_actual).split()
            )

            self.fecha_actual = []
            self.dentro_fecha = False

        # Terminó la noticia completa
        if tag == "article" and self.dentro_article:

            if (
                self.noticia_actual["titulo"]
                and self.noticia_actual["enlace"]
            ):
                self.noticias.append(self.noticia_actual)

            self.noticia_actual = None
            self.dentro_article = False

class EmolParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.noticias = []

        self.dentro_titulo = False
        self.titulo_actual = []
        self.enlace_actual = ""

        self.dentro_hora = False
        self.hora_actual = ""

        self.noticia_actual = None

    def handle_starttag(self, tag, attrs):

        attrs = dict(attrs)

        if tag in ("h1", "h3"):

            self.dentro_titulo = True
            self.titulo_actual = []
            self.enlace_actual = ""

        if self.dentro_titulo and tag == "a" and "href" in attrs:

            self.enlace_actual = urljoin(
                "https://www.emol.com",
                attrs["href"]
            )

        if tag == "span" and "class" in attrs:

            if "color_hora2008" in attrs["class"]:

                self.dentro_hora = True
                self.hora_actual = ""

    def handle_data(self, data):

        if self.dentro_titulo:
            self.titulo_actual.append(data)

        if self.dentro_hora:

            texto = data.strip()

            if re.match(r"^\d{2}:\d{2}", texto):

                self.hora_actual = texto[:5]

    def handle_endtag(self, tag):

        if tag in ("h1", "h3") and self.dentro_titulo:

            titulo = " ".join(
                "".join(self.titulo_actual).split()
            )

            if titulo and self.enlace_actual:

                self.noticia_actual = {
                    "titulo": titulo,
                    "enlace": self.enlace_actual,
                    "hora": ""
                }

            self.titulo_actual = []
            self.enlace_actual = ""
            self.dentro_titulo = False

        if tag == "span" and self.dentro_hora:

            if self.noticia_actual:

                self.noticia_actual["hora"] = self.hora_actual

                self.noticias.append(
                    self.noticia_actual
                )

                self.noticia_actual = None

            self.hora_actual = ""
            self.dentro_hora = False

def descargar():

    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=20) as respuesta:
        return respuesta.read().decode("utf-8")


def es_noticia_chilena(noticia):

    titulo = noticia["titulo"].strip()
    enlace = noticia["enlace"]

    # No aceptar marcadores virtuales
    if "/marcador-virtual-" in enlace:
        return False

    # No aceptar títulos que sean categorías
    categorias = [
        "Copa Chile",
        "Fecha FIFA",
        "Liga de Primera",
        "Ascenso",
        "La Roja",
        "Fútbol Nacional",
        "Fútbol Internacional",
        "Deportes"
    ]

    if titulo in categorias:
        return False

    # Categorías chilenas que queremos
    categorias_chilenas = [
        "/copa-chile/",
        "/liga-de-primera/",
        "/ascenso/",
        "/seleccion-chilena/",
        "/colo-colo/",
        "/universidad-de-chile/",
        "/universidad-catolica/",
        "/everton/",
        "/union-espanola/",
        "/palestino/",
        "/audax-italiano/",
        "/huachipato/",
        "/ohiggins/",
        "/coquimbo-unido/",
        "/union-la-calera/",
        "/la-serena/",
        "/nublense/",
        "/audax/",
        "/palestino/"
    ]

    if not any(categoria in enlace for categoria in categorias_chilenas):
        return False

    return True

def fecha_biobio(fecha):

    if not fecha:
        return ""

    try:
        fecha_texto, hora = fecha.split("|")

        partes = fecha_texto.strip().split()

        dia = partes[1]
        mes = partes[2].replace(",", "")
        anio = partes[3]

        meses = {
            "Enero": "01",
            "Febrero": "02",
            "Marzo": "03",
            "Abril": "04",
            "Mayo": "05",
            "Junio": "06",
            "Julio": "07",
            "Agosto": "08",
            "Septiembre": "09",
            "Octubre": "10",
            "Noviembre": "11",
            "Diciembre": "12"
        }

        return f"{anio}-{meses[mes]}-{dia.zfill(2)} {hora.strip()}"

    except Exception:
        return ""

def es_noticia_chilena_biobio(noticia):

    enlace = noticia["enlace"]
    titulo = noticia["titulo"].lower()

    # Noticias directamente relacionadas con La Roja
    if "/deportes/futbol/la-roja/" in enlace:
        return True

    # Fútbol nacional chileno
    if "/deportes/futbol/futbol-nacional/" in enlace:
        return True

    # Copa Chile
    if "/deportes/futbol/copa-chile/" in enlace:
        return True

    # Ascenso chileno
    if "/deportes/futbol/ascenso/" in enlace:
        return True

    # Liga de Primera
    if "/deportes/futbol/liga-de-primera/" in enlace:
        return True

    # Noticias que representan directamente a Chile
    if "/noticias/nacional/chile/" in enlace and "team chile" in titulo:
        return True

    # Eventos deportivos realizados en Chile
    if "/deportes/mas-deportes/" in enlace:

        eventos_chile = [
            "rallymobil",
            "titan forest",
            "en chile",
            "en santiago",
            "en rancagua",
            "en viña",
            "en valparaíso",
            "en concepción",
            "en temuco",
            "en puerto montt"
        ]

        if any(evento in titulo for evento in eventos_chile):
            return True

    # Artículos de servicio sobre partidos de Chile
    if "/noticias/servicios/toma-nota/" in enlace:

        if "chile" in titulo:
            return True

    return False

def es_noticia_chilena_emol(noticia):

    titulo = noticia["titulo"].lower()
    enlace = noticia["enlace"].lower()

    # No aceptar páginas especiales de Emol
    if "/especiales/" in enlace:
        return False

    # Selección chilena / La Roja / Team Chile
    palabras_chile = [
        "la roja",
        "selección chilena",
        "seleccion chilena",
        "team chile",
        "marcelino núñez",
        "marcelino nunez"
    ]

    if any(palabra in titulo for palabra in palabras_chile):
        return True

    # Copa Chile
    if "copa chile" in titulo or "copa-chile" in enlace:
        return True

    # Clubes y fútbol chileno
    clubes_chilenos = [
        "colo colo",
        "universidad de chile",
        "universidad católica",
        "universidad catolica",
        "cobreloa",
        "wanderers",
        "santiago wanderers",
        "san luis",
        "everton",
        "audax",
        "palestino",
        "huachipato",
        "ohiggins",
        "o'higgins",
        "unión española",
        "union española",
        "unión la calera",
        "union la calera",
        "coquimbo unido",
        "la serena",
        "nublense",
        "ñublense",
        "puerto montt",
        "santiago morning",
        "san felipe",
        "deportes temuco",
        "deportes iquique"
    ]

    if any(club in titulo for club in clubes_chilenos):
        return True

    # Deportistas chilenos
    deportistas_chilenos = [
        "jarry",
        "tabilo",
        "garín",
        "garin",
        "nicolás jarry",
        "nicolas jarry",
        "alejandro tabilo"
    ]

    if any(nombre in titulo for nombre in deportistas_chilenos):
        return True

    return False

html = descargar()

parser = NoticiasParser()
parser.feed(html)

noticias_finales = []
vistos = set()

# BioBioChile
url_biobio = "https://www.biobiochile.cl/lista/categorias/deportes"

req_biobio = urllib.request.Request(
    url_biobio,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(url_biobio, timeout=20) as respuesta:
    html_biobio = respuesta.read().decode("utf-8")

parser_biobio = BioBioParser()
parser_biobio.feed(html_biobio)

for noticia in parser_biobio.noticias:

    if not noticia["fecha"]:
        continue

    if not es_noticia_chilena_biobio(noticia):
        continue

    enlace = noticia["enlace"]

    if enlace in vistos:
        continue

    fecha = fecha_biobio(noticia["fecha"])

    if not fecha:
        continue

    vistos.add(enlace)

    noticias_finales.append({
        "titulo": noticia["titulo"],
        "fuente": "BioBioChile",
        "enlace": enlace,
        "fecha_publicacion": fecha
    })


# Cooperativa
for noticia in parser.noticias:

    if not es_noticia_chilena(noticia):
        continue

    enlace = noticia["enlace"]

    if enlace in vistos:
        continue

    vistos.add(enlace)

    noticias_finales.append({
        "titulo": noticia["titulo"],
        "fuente": "Cooperativa",
        "enlace": enlace,
        "fecha_publicacion": enlace.split("/")[-2] + " " + enlace.split("/")[-1].replace(".html", "")
    })

# Emol
url_emol = "https://www.emol.com/deportes/"

req_emol = urllib.request.Request(
    url_emol,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(req_emol, timeout=20) as respuesta:
    html_emol = respuesta.read().decode("utf-8")

parser_emol = EmolParser()
parser_emol.feed(html_emol)

for noticia in parser_emol.noticias:

    if not es_noticia_chilena_emol(noticia):
        continue

    enlace = noticia["enlace"]

    if enlace in vistos:
        continue

    # Obtener fecha desde la URL de Emol
    partes_url = enlace.split("/")

    try:
        indice_deportes = partes_url.index("Deportes")

        anio = partes_url[indice_deportes + 1]
        mes = partes_url[indice_deportes + 2]
        dia = partes_url[indice_deportes + 3]

    except (ValueError, IndexError):
        continue

    hora = noticia["hora"]

    if not hora:
        continue

    fecha = f"{anio}-{mes}-{dia} {hora}"

    vistos.add(enlace)

    noticias_finales.append({
        "titulo": noticia["titulo"],
        "fuente": "Emol",
        "enlace": enlace,
        "fecha_publicacion": fecha
    })

# Eliminar noticias con más de 48 horas de antigüedad
ahora = datetime.now()

limite = ahora - timedelta(hours=48)

def fecha_noticia(fecha):

    try:
        if len(fecha) == 16:
            return datetime.strptime(
                fecha,
                "%Y-%m-%d %H:%M"
            )

        return datetime.strptime(
            fecha,
            "%Y-%m-%d %H%M%S"
        )

    except ValueError:
        return None


noticias_finales = [
    noticia
    for noticia in noticias_finales
    if fecha_noticia(noticia["fecha_publicacion"])
    and fecha_noticia(noticia["fecha_publicacion"]) >= limite
]

# Ordenar todas las noticias por fecha, de más nueva a más antigua
noticias_finales.sort(
    key=lambda noticia: fecha_noticia(noticia["fecha_publicacion"]),
    reverse=True
)

# Mostrar solamente las 20 más recientes
noticias_finales = noticias_finales[:20]


datos = {
    "actualizado": datetime.now(timezone.utc).isoformat(),
    "noticias": noticias_finales
}


with open("noticias.json", "w", encoding="utf-8") as archivo:

    json.dump(
        datos,
        archivo,
        ensure_ascii=False,
        indent=2
    )


print(f"Noticias encontradas en Cooperativa: {len(parser.noticias)}")
print(f"Noticias chilenas seleccionadas: {len(noticias_finales)}")
print()

for noticia in noticias_finales:
    print("-", noticia["fuente"], "|", noticia["fecha_publicacion"], "|", noticia["titulo"])
