"""
Descarga del último resultado generado en Google Flow.

Flujo: hover card → click more_vert → menuitem Descargar → sub-menú resolución

SELECTORES CRÍTICOS (validados 2026-04-15):
  - more_vert: el ícono es texto <i>more_vert</i>, NO atributo data-icon
  - menuitem: usa role="menuitem", NO el elemento custom <menuitem>
"""
from .browser import get_page

SEL_RESULT_CARD = '[aria-roledescription="draggable"]'
SEL_MORE_MENU   = '[aria-roledescription="draggable"] button:has(i:text-is("more_vert"))'
SEL_DL_ITEM     = '[role="menuitem"]:has-text("Descargar")'
SEL_DL_RES = {
    "1K": '[role="menuitem"]:has-text("1K")',
    "2K": '[role="menuitem"]:has-text("2K")',
    "720p": '[role="menuitem"]:has-text("720p")',
}


def _sel_card(is_video: bool) -> str:
    """Card del asset. El filtro `:has(...)` salta las cards de error de Flow,
    que no tienen miniatura."""
    alt = "Miniatura de video" if is_video else "Imagen generada"
    return f'[aria-roledescription="draggable"]:has(img[alt="{alt}"])'


def _sel_menu_item(icono: str) -> str:
    """Entrada del menú por su ligadura de ícono (el texto cambia con el idioma)."""
    return f':is([role="menuitem"], button, [role="button"]):has(i:text-is("{icono}"))'


async def _open_card_menu(page, card) -> None:
    """Abre el menú de acciones de una card (Descargar, Reutilizar, Papelera…).

    Se usa CLIC DERECHO. El toolbar flotante del hover (favorito / reutilizar /
    "Más") sigue existiendo y abre este mismo menú, pero no sirve para
    automatizar: se renderiza en un portal FUERA del elemento de la card, y su
    botón "Más" comparte texto (`more_vert`) con el menú del proyecto, así que a
    nivel de página no se puede distinguir uno del otro. Pulsar el equivocado
    sería peor que fallar. El menú contextual da las mismas entradas y es
    inequívoco.
    """
    await card.scroll_into_view_if_needed()
    for intento in range(3):
        await card.click(button="right", force=True)
        await page.wait_for_timeout(1_000)
        if await page.locator(_sel_menu_item("download")).count() > 0:
            return
    raise RuntimeError("No pude abrir el menú contextual de la card tras 3 intentos.")


async def download_latest(output_path: str, resolution: str = "1K", is_video: bool = False) -> str:
    """Descarga el último resultado. Retorna el path guardado. Debe llamarse con lock."""
    page = await get_page()

    card = page.locator(_sel_card(is_video)).first
    await card.wait_for(state="visible", timeout=30_000)
    await _open_card_menu(page, card)

    dl_item = page.locator(_sel_menu_item("download")).first
    if await dl_item.count() == 0:
        dl_item = page.locator(SEL_DL_ITEM).first
    if await dl_item.count() == 0:
        await page.keyboard.press("Escape")
        raise RuntimeError("No encontré la opción 'Descargar' en el menú de la card.")

    # "Descargar" abre un submenú de resolución (video: 270p / 720p / 1080p / 4K;
    # imagen: 1K / 2K), pero en algunas versiones baja directo. UNA sola
    # expectativa cubre los dos casos: si el submenú aparece se elige la opción,
    # y si no, la descarga ya arrancó con el primer clic.
    candidatos = [SEL_DL_RES.get(resolution)] + [
        SEL_DL_RES[k] for k in SEL_DL_RES if k != resolution
    ]
    if is_video:
        candidatos.append('[role="menuitem"]:has-text("Tamaño original")')
    candidatos = [c for c in candidatos if c]

    elegido = None
    async with page.expect_download(timeout=120_000) as info:
        await dl_item.click()
        for sel in candidatos:
            loc = page.locator(sel).first
            try:
                await loc.wait_for(state="visible", timeout=4_000)
            except Exception:
                continue
            elegido = sel
            await loc.click()
            break
        # Sin submenú no se hace nada más: el primer clic ya disparó la descarga.
    download = await info.value

    if elegido:
        print(f"  Descarga por submenú: {elegido}")
    await download.save_as(output_path)
    return output_path


async def delete_latest_card(is_video: bool = False) -> None:
    """Borra el último resultado generado en caso de error (fallback) para reintentar.

    No fatal: si el menú cambió y no se puede borrar, se sigue adelante — perder
    la limpieza es molesto, tumbar el run por eso sería peor.
    """
    page = await get_page()

    card = page.locator(_sel_card(is_video)).first
    if await card.count() == 0:
        return

    try:
        await _open_card_menu(page, card)
        del_item = page.locator(_sel_menu_item("delete")).first
        if await del_item.count() == 0:
            del_item = page.locator('[role="menuitem"]:has-text("Eliminar")').first
        if await del_item.count() > 0:
            await del_item.click()
            await page.wait_for_timeout(1_000)
        else:
            await page.keyboard.press("Escape")
    except Exception:
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass
