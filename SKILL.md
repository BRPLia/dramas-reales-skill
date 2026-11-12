---
name: dramas-reales
description: Genera mini-telenovelas verticales de justicia poética (~75s en 10 clips) con Google Flow + Remotion. Personajes fotorrealistas consistentes, diálogo hablado con audio nativo, cierre con moraleja. El estilo está hardcodeado; tú solo escribes el guion. Úsalo cuando el usuario quiera un video de "dramas reales", historia con enseñanza, telenovela corta, o contenido tipo #historia #enseñanza para TikTok/Shorts/Reels.
---

# SKILL — Dramas-Reales 🎭

Convierte a cualquier agente de IA en el director de un formato que ya funciona:
**mini-telenovelas de justicia poética**. Alguien abusa de otro, el abusado pone
un límite, el abusador paga el precio, y el video cierra con una **enseñanza
explícita**. ~75 segundos en **10 clips**, personajes fotorrealistas que se
mantienen idénticos, y el **diálogo en español embebido** en el audio nativo del
modelo de video.

No es un thriller con giro: es una **fábula moral moderna**. El espectador no ve
para sorprenderse, ve para que **se haga justicia** y para mandarle el video a
alguien.

El estilo está **hardcodeado**. Tú no diseñas el pipeline: escribes el
`guion.json` y la skill hace el resto.

## ⚙️ Instálate primero (hazlo tú, agente)
1. `python generar.py doctor` → verifica requisitos. El MODO `video` necesita
   **Node 18+**, **npm** y **FFmpeg (ffprobe en el PATH)**; el MODO `recursos`
   solo Python + Chrome. Instala lo que falte (ver `AGENTS.md` → ONBOARDING).
2. `python setup.py` → instala Playwright, navegador y (si hay Node) Remotion.
3. `python generar.py login` → **el usuario** inicia sesión en Google una vez.
   Queda guardada en `session/`.

> Cada video crea un proyecto nuevo y limpio en Flow. Lo permanente es el login
> y las **láminas** de `recursos/`, no los proyectos.

## 🎬 Los comandos
| Comando | Qué hace |
|---|---|
| `python generar.py check <guion.json>` | **Valida sin gastar créditos.** Córrelo SIEMPRE antes de generar. |
| `python generar.py laminas <guion.json>` | Crea **solo las láminas** (personajes y escenarios) que falten. Son imágenes: 0 créditos. Revísalas antes de pagar los clips. |
| `python generar.py personajes` | Lista los personajes y escenarios **guardados**, con su ficha, para reusarlos en otro video. |
| `python generar.py recursos <guion.json>` | Solo los clips `escena1.mp4 … escena10.mp4` para que el usuario los una en su editor. |
| `python generar.py video <guion.json>` | El **video final** ya unido con Remotion: limpio, sin marcas ni texto. |
| `python generar.py clean [proyecto]` | Borra resultados de `outputs/`. |

Salida en `outputs/<fecha>_<titulo>/`.

---

## 🧠 LA REGLA DEL MONÓLOGO (el corazón del estilo)

> **Un solo personaje habla por clip. Habla en voz alta, con una línea que
> cabe en su ventana de habla. Nadie le contesta dentro de esa toma.**

No es negociable, y por dos razones:

- **Técnica:** con un solo hablante en cuadro el modelo no tiene que decidir a
  qué cara pegarle la voz. El lip-sync deja de fallar y desaparece el segundo
  personaje mudo que mueve la boca.
- **Narrativa:** el monólogo lleva **acción + justificación + intención** en una
  sola respiración. Avanza más trama por segundo que un ping-pong de diálogo.

**Los dos tipos, alterna entre ellos:**

| Tipo | Quién | Qué hace |
|---|---|---|
| **Monólogo de abuso** | El abusador, a la víctima o a sí mismo | Comete el abuso Y lo justifica en la misma línea |
| **Monólogo interno** | La víctima, sola | Piensa en voz alta: lo que aguanta, por qué, y qué va a hacer |

Puede haber 2 personajes en cuadro, pero **solo uno con la boca en movimiento**.
El otro reacciona con el cuerpo, y hay que declararlo en el `motion_prompt`:
`the other character does not speak, only reacts`.

---

## 📐 El arco de 10 beats

Rellena esta plantilla **antes** de escribir una sola línea:

```text
ABUSADOR (quién y qué se cree):
VÍCTIMA (quién y qué aporta que el abusador no valora):
EL RECURSO EN DISPUTA (trabajo / casa / herencia / dinero / tiempo):
LA CREENCIA FALSA DEL ABUSADOR (la frase que el final desmiente):
OBJETO GATILLO (prop físico concreto):
LA MORALEJA (una frase, 15-25 palabras):
```

| # | Beat | Quién habla | Función |
|---|---|---|---|
| 1 | **INJUSTICIA** | Abusador | El abuso YA está pasando en los primeros 2s. Lo comete y lo disfraza de generosidad o de derecho. |
| 2 | **AGUANTE** | Víctima (interno) | Por qué no reacciona. Instala lo que ella aporta y él no valora. |
| 3 | **CREENCIA FALSA** | Abusador, solo | Dice en voz alta la teoría que el final va a destruir. **Este beat hace que el desenlace se sienta merecido.** |
| 4 | **ESCALADA 1** | Abusador | Segundo abuso, más descarado, con el **objeto gatillo** en cuadro. |
| 5 | **ESCALADA 2** | Abusador | Tercer abuso: se le sale la **ambición real** (quiere la casa, la receta, el negocio). |
| 6 | **EL LÍMITE** | Víctima (interno) | Nombra lo que pasa sin eufemismos y **anuncia la decisión**. Punto de giro. |
| 7 | **LA SEPARACIÓN** | Víctima | Ejecuta. **Nueva locación o nuevo estado visible.** Modesta pero digna. |
| 8 | **EL VACÍO** | Terceros | El abusador empieza a pagar. Mejor si lo dicen **testigos externos** (clientes, vecinos), no el narrador. |
| 9 | **INTENTO FALLIDO / PATTERN INTERRUPT** | Nadie (mudo) o el abusador | Intenta revertirlo y no puede. Si va mudo, **declara `"silent": true`**. |
| 10 | **MORALEJA** | El que aprendió | Frase de sabiduría, 15-25 palabras. **Cierra. Sin cliffhanger.** |

Rango válido: **9-11 escenas**. Nunca menos de 9. Cada clip cuesta créditos en
Flow, así que 10 es el default. Referencia al 2026-11-09: Omni 1.2 Flash cobra
**3 créditos por segundo** a 720p (un clip de 8s = 24; el video de ~76s ≈ 230).
Las imágenes (láminas y frames) usan 0 créditos. Flow muestra el costo exacto
antes de generar y puede cambiarlo.

**Presupuesto:** no hay cuota de palabras. Cada línea tiene que **caber en su
ventana de habla** (la duración del clip menos ~2s). Una línea demasiado larga
sale cortada o atropellada; `check` te avisa. UNA sola idea central por video.

### El ritmo: elige la duración por beat
Diez clips de 8s son una base válida. Varía solo cuando la acción lo pida.

| Dur | Palabras | Para qué |
|---|---|---|
| **4s** | 0-8 | Pattern interrupt puro. Una reacción sin diálogo, un objeto que se queda sin recoger. Úsalo 1 vez. Sin diálogo → `"silent": true` |
| **6s** | 8-13 | Golpe seco. La sentencia del testigo, la decisión. Corta antes de que respires |
| **8s** | 14-20 | El caballo de batalla. La mayoría de tus beats |
| **10s** | 18-26 | Aire. La creencia falsa (arrogante y cómoda) y la moraleja (cierra sin prisa) |

**Curva recomendada:** `8-8-10-8-8-8-8-6-4-10`.

### Lo que separó a los videos que funcionaron
Salió de comparar 24 publicaciones de una página nueva (los mejores: 42s de
visualización media; los peores: 20s, con la caída fuerte entre los segundos 4
y 6). Es una observación, no una garantía:

- **Primera frase:** relación entre los personajes + abuso concreto + el objeto.
  Nada de presentar la situación: el abuso ya está pasando.
- **Un objeto que se puede tocar** (la comida, la camioneta, el cuaderno) visible
  desde las primeras escenas. Mostrar el problema, no hablar de él.
- **Cada escena añade un hecho o cambia una decisión.** Borra los discursos
  seguidos que repiten la misma indignación.
- **Dos personajes y un lugar** como base. Un tercero solo si tiene función.
- **Planta la prueba o al testigo antes del final.** Que no aparezca una
  autoridad de la nada a resolver todo por su título.
- **La víctima decide y se ve la consecuencia:** devolver una herramienta,
  abrir una llave, perder un favor. Proporcionada, nunca física.
- **Ortografía completa en el diálogo** (acentos y eñes): mejora la pronunciación.

### La moraleja
Dos mitades: **el error** + **la ley general**.
*"Esto me pasó por aprovecharme del trabajo ajeno. El local atrae a la gente,
pero el trato justo es el que la hace volver."*

Prohibido: hashtags hablados, preguntas al espectador, CTA de suscripción. La
moraleja es la última línea del universo de la historia, no un cierre de canal.

### Temas que rinden (conflicto por un recurso, sin violencia)
Trabajo mal pagado · herencia y escrituras · familiares que se instalan ·
suegras · préstamos que no se devuelven · negocio familiar · trato desigual
entre hermanos · el que se burló y luego necesitó ayuda · esfuerzo invisible
del que cuida.

---

## 🎥 Los tres modos visuales (elige UNO por video)

El modo define el **ancla** (inicio de cada `media_prompt`) y el **suffix**
(final de cada `media_prompt` **y** de cada `description` de personaje).
Decláralo en `metadata.visual_mode`.

### MODO A — `realista_documental` (DEFAULT)
Como si un transeúnte hubiera grabado algo real con un teléfono decente.

- **Ancla:** `Photorealistic candid observational documentary footage of ordinary working-class Latin American people, filmed by a bystander at eye level.`
- **Suffix:** `natural available light, sharp focus, true-to-life skin texture and pores, lived-in worn environment, cluttered authentic props, blurred real crowd in the background, slightly desaturated warm grade, handheld phone camera at eye level, no cinematic color grading, no studio lighting, no beauty retouching`
- **Prohibido:** `cinematic`, `professional`, `studio lighting`, `8k`, `beautiful`, `model` — y también `low quality`, `blurry`, `grainy`.

> El realismo **no** viene de degradar la imagen: viene del **diseño de
> producción**. Mandiles manchados, paredes descascaradas, ollas abolladas,
> sillas de plástico, multitud desenfocada al fondo. Pedir "low quality" da una
> imagen fea *y* menos creíble, porque el grano tapa justo los detalles que
> venden la escena.

### MODO B — `kdrama`
Novela coreana pulida, con **actores ficticios**.
- **Ancla:** `Korean drama (K-drama) cinematic still, vertical 9:16. Soft natural lighting, warm color grade, shallow depth of field.`
- **Suffix:** `fictional Korean-featured actors (not real people), polished K-drama cinematography, soft skin tones, gentle film look, 4k`
- Cada personaje SIEMPRE incluye `fictional Korean actor, not a real person`.

### MODO C — `anime_dbz`
Anime shōnen de los 90s. Cel-shaded siempre, cero fotorrealismo.
- **Ancla:** `1990s shonen anime cel-shaded still, Dragon Ball / Captain Tsubasa art style, vertical 9:16. Bold black ink outlines, flat cel shading, dramatic shadows, exaggerated facial expressions.`
- **Suffix:** `retro 90s anime aesthetic, hand-drawn cel animation look, vibrant saturated colors, visible film grain`
- **Motion:** inyecta `dramatic anime zoom, speed lines, impact frames, glowing energy aura, wind-blown hair`.

---

## 🔒 Consistencia a lo largo de 10 clips

Con 5 clips te salva la suerte. Con 10 hay que **construirla**.

### 1. Wardrobe-lock (el más potente)
**La ropa es el ancla de identidad, no la cara.** El modelo re-dibuja rasgos
faciales en cada generación; lo que el espectador usa para reconocer al
personaje es la prenda.

- Cada personaje tiene **UNA prenda distintiva** con **color + tipo + estado de
  desgaste**: `stained beige canvas apron over a maroon t-shirt`.
- Esa cadena exacta se repite **verbatim** en las 10 escenas. Copy-paste
  literal, sin sinónimos.
- **Nadie se cambia de ropa**, aunque pasen semanas en la historia.
- Cambio de ropa o de estado deliberado = **label nuevo** con su propia lámina.
- **Ninguna prenda lleva texto.** Niégalo explícitamente:
  `a plain solid green jersey with NO lettering, NO numbers and NO printed graphics`.
  Las palabras se deforman distinto en cada clip y la deriva se ve en todas las
  tomas. Prendas que atraen texto: jerseys, gorras, playeras estampadas,
  uniformes.
- **Ancla la complexión a la ropa, no a un adjetivo.** `heavy-set man` deriva;
  `a shirt stretched tight over a large belly, the buttons pulling` no.
- **Cuidado con lo que tape la cara.** Lentes oscuros o gorra con visera baja en
  la lámina = sin mirada en todo el video, y aquí la actuación es la cara.

### 2. Bloque de personaje verbatim
Cada `characters[].description` es un bloque de **60-90 palabras**, en este
orden: `edad y complexión → un rasgo facial memorable → pelo → PRENDA
DISTINTIVA con desgaste → suffix del modo`.

**La lámina manda sobre el prompt de escena.** Lo que esté en
`recursos/<label>.png` gana, aunque el `media_prompt` diga otra cosa. Por eso no
puedes variar un accesorio escena por escena: eso es un label nuevo.

### 3. `set_references` — una lámina por locación
```json
"set_references": {
  "set_puesto_tamales": "A cramped street food stall ... NO people, no readable text, no lettering, no prices, no brand labels anywhere. [suffix del modo]"
}
```
- Cada `media_prompt` menciona **UNA sola** locación.
- Concentra **6+ de los 10 clips** en una locación dominante. Volver al mismo
  lugar es lo que el espectador lee como continuidad.
- La escenografía va en la descripción del set (el mantel de flores, el portón
  turquesa): es lo que hace que dos clips separados se sientan del mismo mundo.
- **CERO props con texto legible.** Un `menú escrito a mano` produce `TAMALES
  $25` en un clip y `$50` en otro. Si la locación pide un cartel, descríbelo
  como `a faded illegible paper sign`.

### 4. ⚠️ Los labels son GLOBALES a `recursos/`
Las láminas viven en la skill, así que **reusar un label entre videos da la
misma cara y la misma locación** — es lo que convierte varios videos en una
serie. Pero también significa que si dos guiones distintos declaran `set_casa`,
el segundo **reusa silenciosamente la lámina del primero** y tu descripción
nueva se ignora.

**Nombra por historia, no por tipo:** `set_casa_abuela`, `set_puesto_tamales`,
`mujer_cocinera_tamales`.

**Memoria de personajes.** Cada lámina se guarda con su ficha (descripción y
voz) en `recursos/personajes.json`. El flujo correcto es:

1. `python generar.py personajes` → mira quién existe ya. Para **reusar** un
   personaje en otra historia, usa el mismo label y copia su ficha tal cual.
2. `python generar.py laminas <guion.json>` → crea solo lo que falta (0 créditos)
   y **se detiene**. Enséñale las láminas al usuario.
3. Si una salió mal (texto en la ropa, cara tapada), bórrala de `recursos/` y
   repite el paso 2. Recién después lanza `video` o `recursos`.

`check` avisa si un label ya existe con otra descripción.

### 5. Progresión temporal por luz
El paso del tiempo se marca con la **hora del día**, no con texto en pantalla.
Beats 1-5 de día, 6-7 al anochecer, 8-10 de día otra vez. Declara la luz en cada
`media_prompt` y mantenla idéntica dentro de cada tramo.

---

## 😤 El villano — diseño del aprovechado

Aplica **cuando la historia lo amerite** (hay un abusador con cara y nombre). El
espectador tiene que saber en los primeros 3 segundos, sin que nadie se lo
explique, que este personaje es un aprovechado. Tres capas, las tres:

**Capa 1 — el cuerpo, anclado a la ropa.** El exceso como algo que la ropa está
sufriendo: `a grease-stained shirt stretched tight over a huge belly, the buttons
straining`, `a thick gold chain half-buried in the neck`, `puffy fingers with a
ring cutting into the skin`. Un detalle de descuido siempre (grasa, sudor,
migas): es lo que empuja de "gordo" a **desagradable**.

**Capa 2 — la conducta física** (esto es lo que de verdad da rabia). Dale
SIEMPRE una de estas en su beat, y ponla en los timestamped beats:

| Acción | Qué comunica |
|---|---|
| Come mientras el otro trabaja | Desprecio puro. La más eficaz |
| Habla con la boca llena, escupe migas | Grosería sin filtro |
| Cuenta dinero despacio delante del que no lo recibe | Poder restregado |
| Se sienta y estira las piernas en el espacio del otro | Invade sin permiso |
| Toca el objeto ajeno como si ya fuera suyo | La ambición se le sale |
| Le da palmaditas en el hombro al que humilla | Falsa generosidad, la peor |

**Capa 3 — la voz: se cree el mejor y no lo es.** Nunca dice "soy malo": dice
cosas razonables desde su cabeza, y por eso da rabia.
- Diminutivo condescendiente: `mija`, `sobrinita`, `tu casita`
- Favor disfrazado: `Te estoy haciendo un favor` · `Otro no te aguantaría`
- Sarcasmo seco: `Ay sí, la indispensable` · `Pobrecita, qué difícil`
- Autoelogio sin pruebas: `Aquí el que sabe soy yo` · `Sin mí no eres nadie`
- Minimización: `No exageres` · `Nomás te lo tomé prestado`

Y no lo hagas competente: **cree** que aporta y en realidad solo cobra. Que se
le note en algo concreto (deja las ollas quemándose mientras cuenta dinero).

**Límites:** su humillación es económica, verbal y social, **nunca física**. No
lo cuelgues de un rasgo étnico, un acento real, una discapacidad ni una
condición médica. Déjalo humano en un detalle al final: en el beat 10, solo y
callado, es donde la moraleja pega.

---

## ✍️ Los dos prompts de cada escena

Cada escena tiene DOS prompts y hacen cosas distintas:

- **`media_prompt`** → la **IMAGEN del frame**, con `@menciones`. Congela
  composición, posiciones izquierda/derecha, identidad y vestuario. **SIN diálogo.**
- **`motion_prompt`** → **anima** ese frame: cámara + acción + el monólogo.
  **CERO `@`** (repetir la mención duplica cuerpos).

### `media_prompt` — el frame (Nano Banana 2, prosa con verbo inicial)
```
Render a [medium shot | medium two-shot | close-up], vertical 9:16.
[Ancla del modo activo.]
Inside @set_locacion, @labelA [posición explícita + pose congelada + expresión],
@labelB [posición explícita + pose congelada, mouth closed].
[Objeto gatillo en cuadro.]
[Fondo vivo: extras desenfocados, tráfico, gente comiendo.]
Eye-level camera, [luz + hora del día + grade] — idéntico en todo el tramo.
[Suffix OBLIGATORIO del modo.]
```

### `motion_prompt` — la animación (Omni Flash, bloques + beats)
```
CLIP [N] of 10 - 8s - 9:16
Use the attached frame as the composition, identity and wardrobe reference.

SHOT: Eye-level handheld shot that slowly pushes in from the two-shot toward a
      chest-up framing of the speaker. No cuts.
      [Un solo personaje: "Static eye-level shot with subtle handheld drift."]

ACTION - timestamped beats (reset to 00:00 for this clip):
00:00-00:01: [Micro-acción física que arranca el clip.]
00:01-00:07: [El hablante habla de corrido mientras hace algo con las manos.
              The other character does not speak, only reacts.]
00:07-00:08: [Remate físico sin palabras.]

AUDIO:
The [descriptor + posición], with a [voz verbatim de characters[].voice],
speaks aloud in Latin American Spanish: "[línea que cabe en la ventana de habla]"
Tone: [único lugar donde va lenguaje emocional].
SFX/Ambience: [fuentes físicas concretas]. Music: No music.

Negative Constraints: only one character speaks, the other keeps their mouth closed;
no subtitles, no caption bars, no on-screen text, no readable signs or lettering in
the scene, no misspelled or invented words, no morphing, no wardrobe changes,
consistent faces, no camera cuts, no watermark.
Keep faces, wardrobe, framing and lighting identical to the attached frame.
Output: 8s, 720p, 9:16.
```

**Reglas propias del estilo:**
- El hablante se nombra por **descriptor + posición** (`The heavy man on the
  left`), nunca por label.
- `speaks aloud` (no `says`): empuja al modelo al registro de monólogo.
- El descriptor de voz se copia **verbatim** de `characters[].voice` en cada clip.
- `no camera cuts` siempre: 8s es exactamente la duración en la que el modelo
  intenta meter un corte.
- **La cámara sí se mueve.** Con dos personajes: empieza en two-shot y hace un
  push-in lento hasta el hablante de pecho para arriba, todo en la misma toma.
  Es lo que aísla al hablante y refuerza la regla del monólogo.
- El habla ocupa 00:01–00:07: **sin silencio largo al inicio**.

### Dos filtros al diálogo antes de generar
1. **`y` + negación pegados** se reinterpretan. `"Contraté a otras y ninguna
   cocina como ella"` sale como `"Contraté a otra sin ninguna..."`. Parte en dos
   frases: `"Contraté a otras. Ninguna cocina como ella."`
2. **Palabras largas con pronombres enclíticos se comen sílabas.**
   `regalármelo` → `regármelo`. Usa la forma corta: `"Regálamelo"`, nunca
   `"Deberías regalármelo"`. Igual con `dárselo`, `explicármelo`.

Lo que sí sale perfecto: números escritos (`doscientos pesos`), diminutivos
(`mijita`), interjecciones (`Ay sí`) y frases de 24 palabras seguidas.

---

## 🧾 Esquema del guion (`guion.json`)

Ver `examples/guion_dramas.json` para un guion completo de 10 beats.

| Campo | Regla |
|---|---|
| `metadata.title` | ASCII limpio `[a-zA-Z0-9-]`. Da nombre a la carpeta de salida |
| `metadata.aspect_ratio` | `"9:16"` (default) |
| `metadata.language` | `"es"` (default) |
| `metadata.visual_mode` | `"realista_documental"` (default), `"kdrama"` o `"anime_dbz"` |
| `metadata.subtitulos` | `false` por defecto = **video limpio**. Ver abajo |
| `metadata.characters[]` | `{label, description, voice}`. `description` = 60-90 palabras con prenda distintiva. `voice` es documental (se copia al `motion_prompt`) |
| `metadata.set_references` | `{label: descripción}`, una por locación, **sin personas** y sin texto legible |
| `metadata.set_reference` | Legacy: un string, da el label `@set`. Sigue funcionando |
| `scenes[].scene` | 1..N en orden |
| `scenes[].beat` | Documental, ayuda a auditar el arco |
| `scenes[].characters_in_scene` | Labels en cuadro. **Máx 2, y solo uno habla** |
| `scenes[].silent` | **Obligatorio en toda escena sin diálogo** |
| `scenes[].duration` | `"4s"`, `"6s"`, `"8s"` (default) o `"10s"`. **Solo los modelos Omni las respetan** |
| `scenes[].media_model` | `"Omni Flash"` (default; hoy es **Omni 1.2 Flash**) o `"Veo 3.1 - Lite"`. Flow retira el 5-dic-2026 `"Omni 1.1 Flash"`, `"Veo 3.1 - Fast"` y `"Veo 3.1 - Quality"` |
| `scenes[].image_model` | `"Nano Banana 2"` (default; hoy selecciona **Nano Banana 2.1**), `"Nano Banana 2 Lite"` o `"Nano Banana Pro"` |
| `scenes[].media_prompt` | El frame, CON `@menciones`, sin diálogo |
| `scenes[].motion_prompt` | La animación, SIN `@`, con el monólogo |

`python generar.py check <guion.json>` valida todo esto (y te dice qué láminas
se reusan y cuántos créditos vas a gastar) **sin generar nada**.

---

## 💬 Subtítulos (opcionales, apagados por defecto)

El video sale **limpio**: el diálogo ya se escucha en el audio nativo, y sin
subtítulos el formato se ve más como grabación real. Si el usuario los quiere:

```jsonc
"metadata": { "subtitulos": true }
```
y una vez: `pip install -r requirements-subs.txt`

Se transcriben **en local** con faster-whisper (modelo `small`, CPU, int8): no
hay API, no hay cuenta, no sale nada de la máquina. Las escenas con
`"silent": true` se saltan solas.

---

## ⚠️ Safety del modelo de video

El modelo **censura narrativas de muerte, asesinato, suicidio o violencia contra
personas AUNQUE la imagen sí pase**. El bloqueo lo dispara el **diálogo que
afirma el daño**, no la estética.

- ❌ Evita en diálogos: `morir`, `muerte`, `matar`, `te mató`, `accidente
  provocado`, `si me pasa algo fue ella`, amenazas explícitas de daño.
- ❌ También se bloquea **exigir o quitar dinero de frente**. Verificado el
  2026-11-12: `Desde hoy me das la mitad de lo que vendas` y `Dame la lata
  completa, yo te guardo el dinero` no pasaron; `Me llevo estos tamales, no te
  los pago` sí. Que el abuso sea sobre **cosas o trabajo**, no una exigencia de
  dinero. Flow reembolsa la escena bloqueada y la skill te avisa al instante.
- ✅ Un funeral o un duelo como **escenario** sí pasa.
- ✅ Reencauza el conflicto a daños NO físicos: traición, abuso económico, robo,
  abandono, herencia, secreto. Que además es donde vive este formato.
- ✅ **La autoridad como resolución funciona muy bien**: un policía levantando
  un acta, una escritura, un contrato. Mantenlo en registro procedimental
  (`deben recoger sus cosas y abandonar la propiedad`), nunca amenazante.
- Si una escena se bloquea: NO cambies la estética — reescribe la **línea de
  diálogo** quitando la afirmación de daño físico y conservando el giro.

## ✅ Criterio de éxito
- `outputs/<proyecto>/assets/escenaN.mp4` para cada escena.
- En modo `video`: además `outputs/<proyecto>/<proyecto>.mp4`.
- `status.json` con `"status": "success"`.

## 🛟 Si algo falla
- *SIN SESION* → `python generar.py login`.
- Una escena se censura o da timeout → el motor reintenta 2 veces; si sigue,
  suaviza el diálogo de esa escena (quita la afirmación de daño) y vuelve a
  correr: las escenas ya descargadas **se saltan solas**, no se pagan dos veces.
- Un personaje cambió de ropa en un clip → borra ese `escenaN.mp4` y vuelve a
  correr. Es el defecto que más rompe la ilusión en 10 tomas.
- Una lámina salió mal (lentes que tapan los ojos, texto en la prenda) →
  bórrala de `recursos/` y corrígela ANTES de dejar correr los 10 clips.
- El modo `video` necesita Node 18+; si no lo hay, usa `recursos` y une tú.

## 📋 Checklist antes de generar
- [ ] Los 10 beats están y cada uno cumple su función.
- [ ] La **creencia falsa del beat 3** es exactamente lo que el beat 8-9 desmiente.
- [ ] El beat 5 revela la ambición real, no repite el 4.
- [ ] **Un solo hablante por clip** en los 10. Cero conversación cruzada.
- [ ] Cada personaje tiene UNA prenda distintiva, verbatim en los 10 clips.
- [ ] Ninguna prenda ni prop lleva texto legible.
- [ ] Cada `media_prompt` menciona exactamente UNA locación `@set_*`.
- [ ] Cero `@` en los `motion_prompt`.
- [ ] Toda escena sin diálogo tiene `"silent": true`.
- [ ] Cada línea cabe en su clip (`check` sin avisos); la moraleja tiene error + ley general.
- [ ] Las láminas se crearon con `laminas` y el usuario las revisó.
- [ ] Ninguna línea afirma muerte o daño provocado.
- [ ] **Test del espectador frío:** alguien que no leyó el título, ¿entiende la
      historia viendo los 10 clips con audio?
- [ ] `python generar.py check` pasa.

## Licencia
MIT. Úsalo, modifícalo y móntale tu propio canal.
