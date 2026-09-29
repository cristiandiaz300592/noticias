import json
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone
from urllib.parse import urljoin


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


html = descargar()

parser = NoticiasParser()
parser.feed(html)

noticias_finales = []
vistos = set()

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

    if len(noticias_finales) >= 20:
        break


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
    print("-", noticia["titulo"])
