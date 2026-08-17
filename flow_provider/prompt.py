"""
Escritura y envío del prompt en Google Flow.

IMPORTANTE: El campo de prompt es un editor Slate <div contenteditable="true">,
NO un input/textarea. No usar .fill() — usar .click() + Ctrl+A + keyboard.type().
"""
import re

from .browser import get_page

SEL_PROMPT = 'div[contenteditable="true"]'
SEL_SUBMIT = 'button:has(> :text-is("arrow_forward"))'

# Menú @ (interfaz nueva de Flow): popover Radix con buscador por nombre.
# Validado en scripts/calibrate_mentions3.py — inserta un chip inline en el prompt.
SEL_MENTION_DIALOG = 'div[role="dialog"]:has(input#add-menu-input)'
SEL_MENTION_SEARCH = 'input#add-menu-input'
_ADD_TO_PROMPT_RE = re.compile(r"(Agregar a la instrucci|Add to instruction|Add to prompt)", re.I)


async def submit_prompt(prompt: str) -> None:
    """Escribe el prompt y hace click en submit. Debe llamarse con lock."""
    page = await get_page()

    # Escribir en el div contenteditable
    prompt_box = page.locator(SEL_PROMPT)
    await prompt_box.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.insert_text(prompt)
    await page.wait_for_timeout(300)

    # Click submit
    submit_btn = page.locator(SEL_SUBMIT)
    await submit_btn.first.click()


async def submit_segments_with_voice(segments: list[dict], voice: str | None = None,
                                     voice_sample: str | None = None) -> None:
    """Escribe texto + @menciones, fija la voz nativa y envía. Con lock.

    Dos decisiones que importan:
      - El texto se inserta de golpe (`insert_text`) en vez de tecleado. Un
        prompt de estilo Vox son ~1500 caracteres: a 20 ms por tecla serían 30 s
        por escena. Solo el `@` de una mención necesita ir tecleado, porque es lo
        que dispara el popover.
      - La voz va AL FINAL, justo antes de enviar: se engancha como chip a la
        instrucción, así que elegirla antes de limpiar el campo la borraría.

    `voice_sample` es la frase del "Diálogo de ejemplo" y fija el idioma con que
    la voz narra. Si va en None se usa el default de `canvas` ("hola a todos").
    """
    from .canvas import DEFAULT_VOICE_SAMPLE, select_voice

    page = await get_page()
    box = page.locator(SEL_PROMPT).first
    await box.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(200)

    for seg in segments:
        if seg["type"] == "text":
            if seg.get("value"):
                await page.keyboard.insert_text(seg["value"])
        elif seg["type"] == "mention":
            await _insert_mention(page, seg["name"])
        else:
            raise ValueError(f"segmento desconocido: {seg!r}")

    await page.wait_for_timeout(300)
    if voice:
        await select_voice(voice, voice_sample if voice_sample is not None else DEFAULT_VOICE_SAMPLE)
    await page.locator(SEL_SUBMIT).first.click()


async def submit_prompt_with_voice(prompt: str, voice: str, voice_sample: str | None = None) -> None:
    """Prompt plano (sin menciones) + voz nativa. Con lock."""
    await submit_segments_with_voice([{"type": "text", "value": prompt}], voice, voice_sample)


async def _insert_mention(page, search_name: str) -> None:
    """Inserta una mención inline: abre el menú @, busca por nombre y confirma.

    `search_name` es el texto con que Flow lista el recurso (ej. nombre de archivo
    o de personaje). El recurso debe existir e indexarse en el proyecto.
    """
    await page.keyboard.type("@", delay=60)
    dialog = page.locator(SEL_MENTION_DIALOG)
    await dialog.wait_for(state="visible", timeout=8_000)

    search = page.locator(SEL_MENTION_SEARCH).first
    await search.fill(search_name)
    await page.wait_for_timeout(1_500)

    add_btn = dialog.locator('button, [role="button"]').filter(has_text=_ADD_TO_PROMPT_RE).first
    try:
        await add_btn.wait_for(state="visible", timeout=8_000)
    except Exception:
        # Varios resultados: fijar el preview clickeando la fila con ese nombre.
        row = dialog.get_by_text(search_name, exact=False).first
        if await row.count() > 0:
            await row.click()
            await page.wait_for_timeout(1_000)
        await add_btn.wait_for(state="visible", timeout=8_000)
    await add_btn.click()
    await page.wait_for_timeout(1_200)


async def submit_prompt_with_mentions(segments: list[dict], submit: bool = True) -> None:
    """Escribe un prompt intercalando texto y menciones @ inline, luego envía.

    `segments`: lista ordenada de
        {"type": "text", "value": str}                 -> se teclea literal
        {"type": "mention", "name": str}               -> se inserta vía menú @
    `name` es el texto de búsqueda del recurso en Flow (resuelto por el core a
    partir del label del guion). Debe llamarse con lock.
    """
    page = await get_page()
    box = page.locator(SEL_PROMPT).first
    await box.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(200)

    for seg in segments:
        if seg["type"] == "text":
            if seg.get("value"):
                await page.keyboard.type(seg["value"], delay=20)
        elif seg["type"] == "mention":
            await _insert_mention(page, seg["name"])
        else:
            raise ValueError(f"segmento desconocido: {seg!r}")

    await page.wait_for_timeout(300)
    if submit:
        await page.locator(SEL_SUBMIT).first.click()
