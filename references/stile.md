# Stile: tema bianco + blu

![anteprima](../docs/anteprima.jpg)

## Token (`gfx/assets/world.css`)
| Token | Valore | Uso |
|---|---|---|
| `--font` | Plus Jakarta Sans (OFL, incluso in `assets/fonts/`) | tutto |
| fondo | `#ffffff` → `#f2f6fc` ai bordi, con glow azzurro in alto a destra e blu in basso a sinistra | `.bg` |
| `--text` | `#0c1f3f`, blu notte | inchiostro |
| `--text-2` | `#0c1f3f` al 58% | testi secondari |
| `--accent` / `--accent-hi` | `#1b6bff` / `#2aa9f5` | numeri, bordi, highlight |
| `--grad` | `linear-gradient(135deg, #0a3fd6, #1b74ff 50%, #2aa9f5)` | parole chiave, sottolineature, contatori, copertina |
| `--band` | `#1b6bff` al 10% | fondi di badge e numeri |
| `--shadow` | tre livelli in blu molto tenue | card |

**Tipografia**:
- titoli 800, tracking -0.025em, con un po' d'aria tra le parole (`word-spacing: 0.06em`): Plus Jakarta Sans è più larga di Inter, e con il tracking stretto di Inter le parole si incollano;
- testi 400-700;
- niente sotto i 30 px.

## Raggi (non cambiano mai)
| Elemento | Raggio |
|---|---|
| card | 32 |
| doc | 40 |
| tile | 72 |
| telefono | 84 |
| cornice delle catture | 36 |
| copertina | 30 |
| card del volto nello split, angoli in alto | 75 |

## Sottotitoli e copertina (`work/burn.py`)
- **Font e misure**: `PlusJakartaSans-800`, 72 px (evidenziati 86 px), tracking -0.02em. Un blocco più largo di 980 px si rimpicciolisce.
- **Su pannello e grafiche**: inchiostro `#0c1f3f`; gli evidenziati in gradiente.
- **Sul volto**: bianco con ombra morbida ma evidente (blur 11, offset 7, inchiostro al 72%), **mai contorno nero**. Gli evidenziati sono in gradiente, con un bordino bianco sottile.
- **Entrata**: ogni blocco passa da scala 0,92 a 1,0 in 0,1 s, mai uno slide.
- **Copertina**: solo sul frame 0. Riquadro bianco y 262-603 con bordo in gradiente; titolo da `reel.json` `cover` (`lines`, e una parola `accent` in gradiente).
- **Grafica su una foto**: `DARK=S04` (o `S04@5.0`) passa ai sottotitoli stile "volto".

## Cambiare stile
1. In `world.css` cambia i token (colori, `--font`) e i file in `@font-face` dentro `assets/fonts.css`. Usa solo font con licenza che ne permetta la distribuzione (OFL).
2. In `burn.py` cambia `FONT`, `INK`, `GRAD` (stop del gradiente in RGB) e il colore dell'ombra della copertina.
3. Nelle scene di `gen.py` cerca i colori scritti a mano (i raggi azzurri di `numero()` sono `rgba(42, 169, 245, …)`).
4. Non toccare i raggi: lo stile cambia i colori, non le forme.
