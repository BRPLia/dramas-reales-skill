# Ficha de estilo — Frutinovelas

Medido con `python generar.py analizar` el 2026-11-15: 5 virales (84 mil a 2,1
millones de vistas, abril–octubre 2026) y 2 del mismo formato que no funcionaron
(17 y 38 vistas). Evidencia en `evidencia/` (local) y cifras en `resumen.json`.

## 1. Qué es
Una historia completa de 1:40–2:40 con personajes 3D estilo Pixar que tienen una
fruta por cabeza y cuerpo humano. Engancha porque **alguien quiere algo concreto
desde la primera frase** y lo que sigue es cómo le sale mal.

Hay dos ramas:
- **Comedia doméstica** (4 de 5 virales, todas de un mismo canal): una joven, su
  mamá y un mandado o negocio que termina en desastre. Groserías suaves y regionalismos.
- **Drama de venganza** (1 de 5, la más vista: 2,1M): traición, la víctima se
  levanta y castiga. Narración interna en off. Cierra en «Continuará...».

## 2. Cifras (mediana · rango de las 5 virales)
| Medida | Mediana | Rango |
|---|---|---|
| Duración | 107 s | 100–157 s |
| Formato | 16:9 horizontal (1280×720) | las 7 analizadas |
| Tomas | 27 | 11–40 |
| Duración de toma | 2,75 s | 1,7–8 s |
| Palabras por minuto | 121 | 99–149 |
| Palabras por frase | 6,3 | 4,6–8,4 |
| Primera voz | 0–2,3 s | ninguna espera más |

Lectura: las tomas cortas no salen así del generador. Los clips de 8 s se
**cortan** en planos y contraplanos de 1–3 s; el diálogo rápido es un efecto de
montaje. El drama (JcEjqnyWUA4) deja los clips casi enteros (toma mediana 8 s).

## 3. Los primeros 3 segundos
- [NR3aQdMGUfs] La protagonista, barriendo, canta su deseo en rima: plata.
- [DTWKR9tVe2w] Misma protagonista, frase rimada: quiere un novio rico.
- [FsFj946i5Pw] Su plan del día: hacerse rica vendiendo empanadas.
- [NZqEBL0YIMs] Pide trabajo de taxista sin saber manejar.
- [JcEjqnyWUA4] In media res: la esposa encuentra al marido en la cama con otra.

**Regla:** la primera frase es el **deseo concreto** de la protagonista (dinero,
un novio, un trabajo) o el conflicto ya en marcha. En 3 de 5 lo dice ella sola.
La rima aparece en 2 de 5 (el mismo personaje): es un sello del canal, no del formato.

## 4. El arco (comedia, ~100 s)
| Tramo | Qué pasa | Ejemplo medido |
|---|---|---|
| 0–10 s | Deseo + la autoridad (mamá) la manda a hacer algo | «ve al mercado» [DTWKR9tVe2w] |
| 10–40 s | Sale al mundo: un vecino, un cliente, alguien que le gusta | el mango [NR3aQdMGUfs] |
| 40–80 s | El plan se tuerce por su lógica literal o su descaro | 12 leches por 12 huevos [DTWKR9tVe2w] |
| 80–100 s | Vuelve a casa y la autoridad descubre el desastre | la mamá y el caldo [NR3aQdMGUfs] |
| último 5 s | Remate: una réplica o un castigo cómico, sin moraleja | «ya estaba así cuando llegué» [NZqEBL0YIMs] |

Cada tramo gira alrededor de **un objeto que se toca**: leche y huevos, la taza
de arroz, las empanadas, el taxi, las tarjetas bloqueadas.

## 5. Personajes y voces
- 2–4 por historia. Protagonista + autoridad (mamá) fijas; el resto entra y sale.
- Se reconocen por **lo que no es fruta**: peinado y ropa (moños con pasadores,
  tubos en el pelo, delantal de cuadros). La ropa no cambia en todo el video.
- Voces: español latino coloquial (mexicano y rioplatense en el mismo canal).

## 6. El look
- **ancla:** `Stylized 3D animated feature-film still, Pixar-like, horizontal 16:9. Anthropomorphic fruit characters: full human bodies with a whole fruit as the head and a complete expressive cartoon face on the fruit skin.`
- **suffix:** `stylized 3D animated feature-film render, Pixar-like cartoon proportions, not photorealistic, everyday humble Latin American home and neighborhood, warm golden afternoon sunlight, soft global illumination, saturated warm palette, shallow depth of field, smooth clean shaders, no on-screen text, no watermark`
- El estilo de render va en el **suffix**, no solo en el ancla: las láminas
  solo reciben la descripción + suffix. Sin «3D animated… not photorealistic»
  ahí, Flow las hizo fotorrealistas (verificado el 2026-11-15).
- **Fija la cabeza-fruta en cada escena.** En la prueba, la abuela papaya (con
  moño y lentes) se volvió una señora humana a mitad de clip. Se arregló
  escribiendo en el `media_prompt` y en el `motion_prompt` de qué fruta es la
  cabeza de cada personaje en cuadro, «never a human head», y `no human heads`
  en las restricciones. Ojo: no pongas «no human faces», que borra las caras.
- Comedia: casa humilde, calle de tierra, tiendita. Drama: hotel, oficina de
  vidrio, lluvia de noche. Los primeros planos de cara son la mitad de las tomas.

## 7. Cómo se adapta a esta skill
- **Se conserva:** duración, 16:9, deseo en la primera frase, objeto que se toca,
  autoridad que descubre el desastre, remate sin moraleja.
- **Se traduce:** el ping-pong de diálogo. Aquí cada clip tiene **un solo
  hablante** (regla del monólogo) y el ida y vuelta sale de cortar entre clips de
  4–6 s, que es como lo hacen los originales.
- **No se copia:** sus personajes, nombres ni frases. La historia es nueva.
- **Safety de Flow:** el drama de venganza («me querían matar») choca con el
  bloqueo de muerte y dinero; la rama de comedia es la que pasa.
- **Créditos:** a 3 créditos/s, 100 s son ~300 créditos. Para probar, 60–75 s.

## 8. Lo que separó a los virales de los que no (solo 2 sin éxito: anecdótico)
- [4Ciyeql_SJE] Mismo look y mismo ritmo (98 s, 27 tomas), pero nadie quiere
  nada: un guardia piña aprende a confiar. Sin objeto, sin chiste, sin conflicto.
- [hzW219C8FmE] Frases genéricas que el espectador no puede usar: «no es lo que
  parece», «hay algo que nunca te conté». 64 s, cierra sin pagar nada.
- La calidad visual **no** fue la diferencia. La historia sí.

## 9. Límites
- 4 de las 5 virales son del mismo canal: la ficha describe sobre todo su fórmula.
- Solo YouTube; TikTok puede preferir vertical.
- Los cortes se miden con el detector de escena de ffmpeg: una toma «larga» puede
  ser un plano fijo o cortes entre planos muy parecidos.
- La transcripción es automática: los nombres propios salen mal.
