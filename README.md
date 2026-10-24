# MMGestoria · Web de gestión integral

Web estática en español, con el logotipo de MMG recreado en SVG a partir de la referencia facilitada. Colores blanco, azul corporativo y azul marino. Diseño adaptable a móvil, tableta y ordenador.

## Contenido

19 páginas HTML: portada; catálogo con filtros; once páginas de servicios; fiscalidad en régimen común y foral; contacto; aviso legal; privacidad; cookies; y página de error 404.

Áreas: fiscal, contable, laboral y Seguridad Social, autónomos y pymes, extranjería y nacionalidad, tráfico y vehículos, comunidades y alquileres, gestiones administrativas, ayudas y subvenciones, gestiones internacionales y gestión de inmuebles. La página internacional incluye emigración y movilidad, UE, Estados Unidos, documentación y coordinación de apostillas, legalizaciones y traducciones.

Se han evitado opiniones de clientes inventadas, cifras de experiencia sin comprobar, promesas de resultados y afirmaciones de habilitación profesional no aportadas. Las gestiones internacionales se ofrecen previo estudio del caso.

## Abrir y editar

La web generada está en `dist/`. Se puede servir desde cualquier alojamiento estático. Para comprobarla localmente:

```bash
python3 build.py
python3 tools/check_site.py
python3 -m http.server 8000 --directory dist
```

Después, abre `http://localhost:8000/` en tu navegador. No hace falta instalar paquetes para generar, verificar o servir la web. Los iconos SVG, PNG e ICO ya están incluidos; el script opcional `tools/make_icons.py` requiere Pillow e Inkscape únicamente si se desean volver a exportar.

- Textos de servicios y preguntas: `src/content.py`.
- Composición de páginas y metadatos: `build.py`.
- Diseño adaptable: `src/assets/styles.css`.
- Filtros, menú y formulario: `src/assets/app.js`.
- Marca, dominio, contacto y configuración: `site.config.json`.

Después de editar, ejecuta `python3 build.py`. No edites solo `dist/`, porque se regenera.

## Criterios de redacción e identidad

La voz de MMGestoria se redacta siempre en primera persona del plural: nos encargamos, revisamos, te explicamos. El favicon utiliza los mismos trazados y proporciones del logo MMG, con las dos M negras y la G azul sobre un cuadrado blanco; solo se refuerzan los trazos para tamaños pequeños. No se incluye el bloque biográfico de presentación personal. La fiscalidad se presenta en régimen común y en los regímenes forales de Navarra y del País Vasco. El titular principal elegido por Manuel es «Gestión integral. Atención cercana.»; la página de servicios utiliza «Simplificamos tus trámites. Te acompañamos en cada paso.».

## Estado de esta entrega

Es una versión de revisión privada. Se entrega con `public: false`, etiquetas `noindex` y un `robots.txt` que impide el rastreo. El dominio definitivo y los datos públicos de contacto siguen pendientes. El formulario está conectado a Web3Forms mediante la clave facilitada por Manuel y dirige las consultas al correo asociado a esa clave.

No se han publicado los datos de clientes, documentos personales, información económica privada ni credenciales. El teléfono y el correo del titular quedan sin incorporar hasta que Manuel confirme los que quiere publicar.

## Publicación en GitHub Pages

1. Crea un repositorio de GitHub con la rama principal `main` y sube el contenido de este proyecto, incluida la carpeta `.github`. No hace falta subir ninguna carpeta `.openai`.
2. En el repositorio, abre **Settings → Pages → Build and deployment → Source** y elige **GitHub Actions**.
3. El flujo `.github/workflows/pages.yml` genera y verifica la web y publica exclusivamente `dist/`. Al subir los archivos se iniciará el flujo; también puedes iniciarlo desde **Actions → Publicar MMGestoria en GitHub Pages → Run workflow**.
4. Con `public: false`, GitHub puede alojar la versión, pero sus páginas continúan marcadas para no indexarse. Esta etiqueta no es una medida de privacidad: una web en GitHub Pages puede ser accesible públicamente. Revisa el contenido antes de subirlo.
5. Para el lanzamiento, configura los datos reales que se detallan a continuación y cambia `public` a `true`.

La vista privada de Sites es una forma de revisar esta entrega. La publicación futura en la cuenta de GitHub de Manuel se hace con el paquete exportado; esta entrega no ha creado un repositorio en su cuenta personal de GitHub.

## Dominio y puesta en marcha

En `site.config.json`:

- `site_url`: URL HTTPS definitiva, sin barra final. Si utilizas GitHub Pages sin dominio propio y es un repositorio de proyecto, incluye también su ruta, por ejemplo `https://usuario.github.io/repositorio`.
- `contact_email`: correo profesional que se mostrará en la web y para cuestiones de privacidad.
- `contact_phone`: teléfono público, si quieres mostrarlo. Es opcional.
- `web3forms_access_key`: clave pública del formulario de Web3Forms, ya configurada. El correo destinatario se gestiona en Web3Forms.
- `legal_nif` y `legal_address`: identificación y domicilio completos del titular para el aviso legal.
- `google_verification`: código de verificación de Search Console solo si eliges verificar mediante etiqueta HTML. La verificación por DNS no lo requiere.
- `public`: activar únicamente al preparar el lanzamiento.

La generación de una versión pública se detiene si faltan dominio, correo, receptor del formulario, NIF o domicilio. No se han inventado estos datos. Antes de lanzar, confirma el alcance de los servicios y revisa los textos legales y las condiciones del proveedor de formularios para la configuración contratada.

Al generar la versión pública, se crean automáticamente las etiquetas canónicas, las URLs de Open Graph, los datos estructurados y `sitemap.xml` para el dominio configurado. Se habilita el rastreo en `robots.txt`. Si se trata de un dominio propio se genera `dist/CNAME`; el dominio también debe configurarse en **Settings → Pages → Custom domain**, con los registros DNS y el HTTPS indicados por GitHub.

## Formularios y recepción por correo

El formulario está conectado a `https://api.web3forms.com/submit` con la clave pública facilitada por Manuel. El correo receptor es el asociado a esa clave; no se configura otro destinatario desde la web.

Campos enviados: `nombre`, `apellidos`, `email`, `telefono` opcional, `situacion`, `necesitas`, `ciudad` opcional, `caso` y `privacidad`. También se envían `access_key`, `subject` y `from_name`. El campo trampa `botcheck` se mantiene sin marcar y no se envía en las solicitudes legítimas.

Se conservan todas las áreas de servicio, incluida gestión de inmuebles. La voz de la web es plural: «Cuéntanos tu caso», «Nos encargamos», «Nos pondremos en contacto».

El envío con JavaScript se realiza directamente desde el navegador con JSON. El éxito requiere una respuesta HTTP correcta y `success: true` de Web3Forms; un rechazo, error de red o respuesta ilegible conserva el formulario. Sin JavaScript, el formulario conserva su método POST y destino nativo.

La clave de acceso de Web3Forms está diseñada para publicarse en el HTML y equivale a un identificador del destinatario, no a una clave de administración. No se han incluido contraseñas ni credenciales de administración del proveedor.

El proveedor gestiona sus propios límites y filtros antispam. La política de privacidad identifica Web3Forms y enlaza con su política y acuerdo de tratamiento. No se han habilitado integraciones adicionales ni herramientas de seguimiento.

Comprobación local del contrato de envío, sin mandar correos:

```bash
node tools/test_form.mjs
```

Una respuesta aceptada por la API confirma la recepción de la solicitud por Web3Forms; la llegada a la bandeja de entrada se verifica aparte. El 24/10/2026 se envió una única solicitud identificada como prueba técnica, sin datos de clientes, desde el formulario del navegador. Web3Forms la aceptó y se mostró la confirmación. No se ha comprobado la bandeja de entrada del correo asociado a la clave.

## Posicionamiento

Los contenidos importantes se sirven como HTML completo. Cada servicio tiene su propia URL, título, descripción, encabezado principal, preguntas y enlaces relacionados. También se incluyen rutas de navegación y datos estructurados de organización, sitio y servicio, sin valoraciones o reseñas inventadas.

Tras conectar el dominio y activar la versión pública:

1. Verifica el dominio en Google Search Console.
2. Envía el `sitemap.xml` del dominio definitivo.
3. Inspecciona la portada y las páginas prioritarias y solicita su indexación.
4. Comprueba las consultas y páginas que generan visitas antes de añadir más contenidos.

La entrega prepara la base técnica y de contenido. Google decide la indexación y las posiciones; no hay una promesa de aparecer primero.

## Verificación realizada

- Generación y comprobación de las 19 páginas.
- Enlaces internos, recursos, anclas, títulos únicos, metadescripciones, formularios etiquetados, iconos y datos estructurados.
- Navegación, filtros, preguntas desplegables, validación y revisión de solicitudes en navegador.
- Diseño en ordenador y en un marco de 390 píxeles; menú móvil.
- La publicación en el dominio definitivo y la comprobación de la bandeja de entrada del correo receptor se realizan aparte.

## Referencias oficiales consultadas

- [Configuración de GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
- [Flujo estático oficial de GitHub Pages](https://github.com/actions/starter-workflows/blob/main/pages/static.yml).
- [Envío con JavaScript de Web3Forms](https://docs.web3forms.com/how-to-guides/js-frameworks/svelte).
- [Clave pública de Web3Forms](https://docs.web3forms.com/getting-started/faq).
- [Privacidad de Web3Forms](https://web3forms.com/privacy).
- [Acuerdo de tratamiento de Web3Forms](https://web3forms.com/dpa).
- [Guía SEO de Google](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).
- [Modelos de información de protección de datos de la AEPD](https://www.aepd.es/derechos-y-deberes/modelos-y-formularios).
- [Guía de cookies de la AEPD](https://www.aepd.es/guias/guia-cookies.pdf).
