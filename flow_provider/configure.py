"""
Selección de modo (IMAGE/VIDEO), aspect ratio, cantidad y modelo en el panel de Flow.
"""
from .browser import get_page

# Selectores validados (DOM real, 2026-04-15)
SEL_PANEL_TRIGGER = (
    'button[aria-haspopup="menu"]:has-text("Video"), '
    'button[aria-haspopup="menu"]:has-text("Nano Banana"), '
    'button[aria-haspopup="menu"]:has-text("Imagen"), '
    'button[aria-haspopup="menu"]:has-text("Veo")'
)

SEL_TAB_IMAGE       = '[id$="-trigger-IMAGE"]'
SEL_TAB_VIDEO       = '[id$="-trigger-VIDEO"]'
SEL_TAB_FRAMES      = '[id$="-trigger-VIDEO_FRAMES"]'
SEL_TAB_INGREDIENTS = '[id$="-trigger-VIDEO_REFERENCES"]'

SEL_RATIO = {
    "16:9": '[id$="-trigger-LANDSCAPE"]',
    "4:3":  '[id$="-trigger-LANDSCAPE_4_3"]',
    "1:1":  '[id$="-trigger-SQUARE"]',
    "3:4":  '[id$="-trigger-PORTRAIT_3_4"]',
    "9:16": '[id$="-trigger-PORTRAIT"]',
}
SEL_COUNT = {i: f'[id$="-trigger-{i}"]' for i in range(1, 5)}

SEL_MODEL_IMG = {
    'Nano Banana Pro': '[role="menuitem"]:has-text("Nano Banana Pro")',
    'Nano Banana 2':   '[role="menuitem"]:has-text("Nano Banana 2")',
    'Imagen 4':        '[role="menuitem"]:has-text("Imagen 4")',
}
SEL_MODEL_VID = {
    'Veo 3.1 - Lite':    '[role="menuitem"]:has-text("Veo 3.1 - Lite")',
    'Veo 3.1 - Fast':    '[role="menuitem"]:has-text("Veo 3.1 - Fast")',
    'Veo 3.1 - Quality': '[role="menuitem"]:has-text("Veo 3.1 - Quality")',
    'Omni Flash':        '[role="menuitem"]:has-text("Omni Flash")',
}


import re

async def _click_menu_option(page, sel_id: str, texts: list[str]) -> None:
    """Intenta hacer click en una opción del menú por su selector de ID, y si falla o no es visible, busca por texto y rol."""
    loc_id = page.locator(sel_id)
    if await loc_id.count() > 0 and await loc_id.first.is_visible():
        await loc_id.first.click()
        return
        
    regex = re.compile("|".join(texts), re.IGNORECASE)
    
    # Intentar buscar por roles interactivos comunes y coincidencia de texto
    for role in ["tab", "menuitem", "button"]:
        loc_role = page.locator(f'[role="{role}"]').filter(has_text=regex)
        if await loc_role.count() > 0 and await loc_role.first.is_visible():
            await loc_role.first.click()
            return
            
    # Fallback general de elementos que contengan el texto
    loc_text = page.locator('button, [role="button"], span, div').filter(has_text=regex)
    if await loc_text.count() > 0 and await loc_text.first.is_visible():
        await loc_text.first.click()
        return
        
    # Si todo falla, hacer click con el selector de ID para que Playwright arroje el error detallado
    await loc_id.first.click()


async def _dismiss_blocking_changelog(page) -> None:
    """Detecta y elimina de forma destructiva del DOM cualquier modal o iframe de changelog que bloquee la pantalla."""
    try:
        # 1. Intentar cerrar con Escape primero
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        
        # 2. Evaluar JS para eliminar el iframe del changelog y su contenedor flotante del DOM
        await page.evaluate("""() => {
            const iframes = document.querySelectorAll('iframe[src*="changelogs"]');
            iframes.forEach(iframe => {
                let parent = iframe.parentElement;
                let foundParent = false;
                while (parent && parent !== document.body) {
                    const role = parent.getAttribute('role');
                    const className = parent.className || '';
                    if (role === 'dialog' || className.includes('dialog') || className.includes('eoilMe') || className.includes('sc-')) {
                        parent.remove();
                        foundParent = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                if (!foundParent) {
                    iframe.remove();
                }
            });
        }""")
        await page.wait_for_timeout(300)
    except Exception:
        pass


async def select_image_mode(
    aspect_ratio: str = "9:16",
    count: int = 1,
    model: str = "Nano Banana 2",
) -> None:
    """Abre el panel y configura modo IMAGE. Debe llamarse con lock."""
    page = await get_page()
    await _dismiss_blocking_changelog(page)

    # Abrir panel
    trigger = page.locator(SEL_PANEL_TRIGGER)
    await trigger.first.click()
    await page.wait_for_timeout(500)

    # Seleccionar tab IMAGE
    await _click_menu_option(page, SEL_TAB_IMAGE, ["Imagen", "Image"])
    await page.wait_for_timeout(300)

    # Aspect ratio
    ratio_sel = SEL_RATIO.get(aspect_ratio)
    if not ratio_sel:
        raise ValueError(f"aspect_ratio '{aspect_ratio}' no válido. Opciones: {list(SEL_RATIO)}")
    await _click_menu_option(page, ratio_sel, [aspect_ratio])
    await page.wait_for_timeout(300)

    # Seleccionar modelo
    model_sel = SEL_MODEL_IMG.get(model)
    if model_sel:
        model_trigger = page.locator('[role="menu"] button[aria-haspopup="menu"], [role="menu"] button[aria-expanded]')
        if await model_trigger.count() > 0:
            await model_trigger.first.click()
            await page.wait_for_timeout(300)
            await page.locator(model_sel).first.click()
            await page.wait_for_timeout(300)

    # Cantidad
    count_sel = SEL_COUNT.get(count)
    if count_sel:
        await _click_menu_option(page, count_sel, [f"{count}x", f"{count} var", str(count)])
        await page.wait_for_timeout(300)

    # Cerrar panel
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)


async def _select_duration(page, duration: str) -> None:
    """Best-effort: elige la duración del clip (ej. '6s'/'8s') en el panel de video.

    NO-FATAL por diseño: si no encuentra el control (DOM cambió o el modelo no
    soporta duración), no rompe nada — Flow usa su duración por defecto. Solo se
    invoca cuando `duration` viene explícito (hoy solo el motor DramasReales con
    Omni Flash). Selector pendiente de calibración contra el DOM real de Flow.
    """
    num = re.sub(r"[^0-9]", "", duration or "")
    if not num:
        return
    regex = re.compile(rf"^\s*{num}\s*(s|seg|segundos)?\s*$", re.IGNORECASE)
    try:
        # Abrir el sub-dropdown de duración si existe (suele mostrar el valor actual "Ns").
        trig = page.locator('button[aria-haspopup="menu"]').filter(
            has_text=re.compile(r"\b\d+\s*s\b|Duraci|Duration", re.IGNORECASE)
        )
        if await trig.count() > 0 and await trig.first.is_visible():
            await trig.first.click()
            await page.wait_for_timeout(300)
        # Click en la opción que coincide con la duración pedida.
        for role in ["menuitem", "option", "tab", "button"]:
            loc = page.locator(f'[role="{role}"]').filter(has_text=regex)
            if await loc.count() > 0 and await loc.first.is_visible():
                await loc.first.click()
                await page.wait_for_timeout(300)
                return
        loc = page.locator('button, [role="button"], span, div').filter(has_text=regex)
        if await loc.count() > 0 and await loc.first.is_visible():
            await loc.first.click()
            await page.wait_for_timeout(300)
    except Exception:
        pass  # no-fatal: se conserva la duración por defecto de Flow


async def select_video_mode(
    mode: str = "texto",
    model: str = "Veo 3.1 - Lite",
    aspect_ratio: str = "9:16",
    count: int = 1,
    duration: str | None = None,
) -> None:
    """Abre el panel y configura modo VIDEO. Debe llamarse con lock."""
    page = await get_page()
    await _dismiss_blocking_changelog(page)

    # Abrir panel
    trigger = page.locator(SEL_PANEL_TRIGGER)
    await trigger.first.click()
    await page.wait_for_timeout(500)

    # Seleccionar tab VIDEO
    await _click_menu_option(page, SEL_TAB_VIDEO, ["Video"])
    await page.wait_for_timeout(300)

    # Sub-tab de modo
    if mode == "fotogramas":
        await _click_menu_option(page, SEL_TAB_FRAMES, ["Fotogramas", "Frames"])
    elif mode == "ingredientes":
        await _click_menu_option(page, SEL_TAB_INGREDIENTS, ["Ingredientes", "References", "Ingredients"])
    await page.wait_for_timeout(300)

    # Aspect ratio
    ratio_sel = SEL_RATIO.get(aspect_ratio)
    if not ratio_sel:
        raise ValueError(f"aspect_ratio '{aspect_ratio}' no válido.")
    await _click_menu_option(page, ratio_sel, [aspect_ratio])
    await page.wait_for_timeout(300)

    # Seleccionar modelo
    model_sel = SEL_MODEL_VID.get(model)
    if model_sel:
        model_trigger = page.locator('[role="menu"] button[aria-haspopup="menu"], [role="menu"] button[aria-expanded]')
        if await model_trigger.count() > 0:
            await model_trigger.first.click()
            await page.wait_for_timeout(300)
            await page.locator(model_sel).first.click()
            await page.wait_for_timeout(300)

    # Cantidad
    count_sel = SEL_COUNT.get(count)
    if count_sel:
        await _click_menu_option(page, count_sel, [f"{count}x", f"{count} var", str(count)])
        await page.wait_for_timeout(300)

    # Duración del clip (best-effort, solo si se pide explícito; ej. Omni Flash 6s/8s)
    if duration:
        await _select_duration(page, duration)

    # Cerrar panel
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
