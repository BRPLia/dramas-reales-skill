"""
Espera de resultados de generación en Google Flow.

Flow tiene 3 fases post-submit para imágenes:
  Fase 1: card con blur + contador % (6 → 99)
  Fase 2: reveal animation ~5s — img aparece pero toolbar NO interactivo
  Fase 3: imagen lista — toolbar (more_vert) visible al hover

Incluye detección de errores de generación ("No se pudo generar") con retry automático.
"""
import asyncio
import random
import re
import time

from .browser import get_page

SEL_RESULT_IMAGE = 'img[alt="Imagen generada"]'
SEL_RESULT_VIDEO = 'img[alt="Miniatura de video"]'
SEL_RESULT_CARD  = '[aria-roledescription="draggable"]'
SEL_MORE_MENU    = '[aria-roledescription="draggable"] button:has(i:text-is("more_vert"))'

# Selectores de error de generación — usar texto literal para evitar falsos positivos
# con cards de loading que también tienen data-tile-id
SEL_ERROR_TEXT = ':text("No se pudo generar")'
_ERROR_CARD_RE = re.compile(r"No se pudo generar|Se produjo un error", re.IGNORECASE)
# La card de error trae tres botones; el útil es "Reutilizar instrucción":
# devuelve al campo TODA la instrucción, incluida la voz elegida.
_REUSE_RE = re.compile(
    r"(Reutilizar instrucci|Volver a usar|Reuse (the )?prompt|Reuse instruction)", re.IGNORECASE
)
# DOM real de la card (calibrado 2026-07-31): tres botones, cada uno con su
# ligadura de ícono y una etiqueta accesible oculta.
#   refresh        -> "Reintentar"
#   undo           -> "Reutilizar instrucción"   <- el que sirve
#   delete_forever -> "Borrar"
_REUSE_ICON = 'button:has(i:text-is("undo"))'


async def error_card_count(page) -> int:
    """Cards de error visibles ahora mismo.

    Se usa como LÍNEA BASE antes de esperar: las cards de error de escenas o
    intentos anteriores siguen en el canvas hasta que se refresca la página, y
    sin este baseline hacían fallar la escena siguiente en segundos sin que esa
    generación tuviera nada malo.
    """
    return await page.locator(SEL_ERROR_TEXT).count()


async def _reuse_instruction_and_resend(page, attempt: int = 0) -> bool:
    """Recupera una generación que Flow tumbó por saturación.

    Flow devuelve seguido una card "No se pudo generar / Se produjo un error"
    cuando está saturado; no es un rechazo del prompt. Esa card trae el botón
    "Reutilizar instrucción", que repone la instrucción completa (prompt + voz)
    en el campo. Desde ahí solo falta reenviar. Es exactamente la maniobra
    manual que funciona.
    """
    card = page.locator(SEL_RESULT_CARD).filter(has_text=_ERROR_CARD_RE).first
    if await card.count() == 0:
        return False

    btn = card.locator(_REUSE_ICON).first
    via = "ícono undo"
    if await btn.count() == 0:
        btn = card.get_by_role("button", name=_REUSE_RE).first
        via = "nombre accesible"
    if await btn.count() == 0:
        print("  [flow] Card de error sin botón 'Reutilizar instrucción' localizable.")
        return False

    # El botón de enviar arranca con aria-disabled="true" y se habilita cuando la
    # instrucción vuelve al campo. Esperar eso es más fiable que un sleep:
    # confirma que Flow repuso de verdad el prompt y la voz.
    from .prompt import SEL_SUBMIT
    submit = page.locator(SEL_SUBMIT).first
    try:
        await submit.wait_for(state="visible", timeout=15_000)
    except Exception:
        print("  [flow] No encuentro el botón de enviar.")
        return False

    async def _campo_listo(segundos: float) -> bool:
        for _ in range(int(segundos * 2)):
            try:
                if await submit.get_attribute("aria-disabled") != "true":
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
        return False

    # Dos pulsaciones: el primer clic a veces cae mientras la card todavía se
    # está montando y no repone nada. Rendirse ahí desperdicia el reintento.
    for pulsacion in range(2):
        await btn.click(force=True)
        if await _campo_listo(20.0):
            break
        if pulsacion == 0:
            print("  [flow] El campo siguió vacío; vuelvo a pulsar 'Reutilizar instrucción'.")
            await asyncio.sleep(2.0)
    else:
        print("  [flow] 'Reutilizar instrucción' no repuso la instrucción tras dos intentos.")
        return False

    # Respiro antes de reenviar. Flow devuelve este error cuando está saturado,
    # así que reintentar en el acto suele volver a fallar; el retardo crece con
    # cada intento y lleva algo de azar para no reenviar siempre en el mismo
    # instante exacto.
    espera = random.uniform(4.0, 9.0) * (attempt + 1)
    print(f"  [flow] Instrucción reutilizada (vía {via}). Reenviando en {espera:.1f}s...")
    await asyncio.sleep(espera)

    await submit.click()
    await page.wait_for_timeout(2_000)
    return True


async def _poll_until_ready(page, media_sel: str, pre_cards, pre_errors: int, timeout_ms: int) -> str:
    """Espera a que aparezca el asset nuevo o una card de error NUEVA.

    Devuelve 'ok' o 'error'. Lanza TimeoutError si no pasa ninguna de las dos.

    Se hace por polling y no con `locator.or_()` porque `or_` se satisface con
    cualquier miniatura vieja del canvas: a partir de la escena 2 daba por buena
    la generación en el acto y desactivaba la detección de errores.
    """
    guard = "true" if pre_cards is None else f"cards.length > {pre_cards}"
    js = f"""() => {{
        const cards = document.querySelectorAll('{SEL_RESULT_CARD}');
        if (!cards.length) return false;
        if (!({guard})) return false;
        return !!cards[0].querySelector('{media_sel}');
    }}"""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if await page.evaluate(js):
            return "ok"
        if await error_card_count(page) > pre_errors:
            return "error"
        await asyncio.sleep(2)
    raise TimeoutError(f"Generación no completó en {timeout_ms // 1000}s")


async def _wait_for_media(media_sel: str, kind: str, timeout_ms: int,
                          max_retries: int, pre_submit_count) -> None:
    page = await get_page()
    pre_errors = await error_card_count(page)

    for intento in range(max_retries + 1):
        estado = await _poll_until_ready(page, media_sel, pre_submit_count, pre_errors, timeout_ms)
        if estado == "ok":
            return
        if intento >= max_retries:
            raise Exception(
                f"Generación de {kind} falló {max_retries + 1} veces seguidas. "
                "Flow reporta: 'No se pudo generar' (suele ser saturación)."
            )
        print(f"  [flow] Error de generación ({intento + 1}/{max_retries + 1}). Recuperando...")
        if not await _reuse_instruction_and_resend(page, intento):
            raise Exception(
                "Flow reporta 'No se pudo generar' y no pude reutilizar la instrucción."
            )
        # La card de error nueva pasa a formar parte del paisaje: si no se
        # recuenta, el siguiente poll la volvería a leer como fallo inmediato.
        pre_errors = await error_card_count(page)


async def wait_for_image(timeout_ms: int = 90000, max_retries: int = 2, pre_submit_count: int | None = None) -> None:
    """Espera la imagen generada. Recupera sola si Flow falla por saturación."""
    await _wait_for_media(SEL_RESULT_IMAGE, "imagen", timeout_ms, max_retries, pre_submit_count)
    page = await get_page()
    # Confirmar que el bitmap está decodificado antes de dejar seguir al motor.
    try:
        await page.wait_for_function(
            f"""() => {{
                const card = document.querySelector('{SEL_RESULT_CARD}');
                const img = card && card.querySelector('{SEL_RESULT_IMAGE}');
                return img && img.complete && img.naturalWidth > 0;
            }}""",
            timeout=60_000,
        )
    except Exception:
        pass


async def wait_for_video(timeout_ms: int = 360000, max_retries: int = 2, pre_submit_count: int | None = None) -> None:
    """Espera el video generado. Recupera sola si Flow falla. Default 6 min."""
    await _wait_for_media(SEL_RESULT_VIDEO, "video", timeout_ms, max_retries, pre_submit_count)
    page = await get_page()
    try:
        await page.wait_for_function(
            f"""() => {{
                const card = document.querySelector('{SEL_RESULT_CARD}');
                const vid = card ? card.querySelector('video') : document.querySelector('video');
                if (!vid) return false;
                return vid.readyState >= 2 || (vid.src && vid.src.length > 0);
            }}""",
            timeout=80_000,
        )
    except Exception:
        pass  # Fallback: Flow a veces renderiza miniatura y oculta src
