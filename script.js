const estado = document.getElementById("estado");
const contenedor = document.querySelector(".noticias");

fetch("./noticias.json")
    .then(respuesta => respuesta.json())
    .then(datos => {

        contenedor.innerHTML = "<h2>Últimas noticias</h2>";

        if (!datos.noticias || datos.noticias.length === 0) {
            estado.textContent = "No hay noticias disponibles.";
            return;
        }

        datos.noticias.forEach(noticia => {

            const articulo = document.createElement("article");
            articulo.className = "noticia";

            articulo.innerHTML = `
                <h3>
                    <a href="${noticia.enlace}" target="_blank">
                        ${noticia.titulo}
                    </a>
                </h3>

                <p class="fuente">
                    ${noticia.fuente}
                </p>
            `;

            contenedor.appendChild(articulo);
        });

        estado.textContent =
            `Última actualización: ${new Date(datos.actualizado).toLocaleString("es-CL")}`;
    })
    .catch(error => {

        console.error(error);

        estado.textContent =
            "No se pudieron cargar las noticias.";
    });
