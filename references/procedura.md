# Procedura tecnica

Dettagli di ogni passo, misure della reference e gotcha. Vengono da un reel di circa 2 minuti montato interamente in codice.

## 1. Lo studio della reference
Prendi **una** reference sola e studiala a **tutti** i frame, non a campione:
- `ffmpeg -i ref.mp4 -vf "scale=216:384,tile=10x6" ref/sheet_%02d.jpg`, cioè 60 frame per foglio;
- i frame chiave a piena risoluzione.

Le misure qui sotto vengono da una reference a 30 fps di un creator del genere. Sono i default del template.

### Layout
- **SPLIT**:
  - pannello grafico in alto, y 0 → ~1010, con fondo piatto;
  - card del volto in basso, y ~1010 → 1920, a tutta larghezza, **solo gli angoli in alto arrotondati, raggio ~75 px**, senza bordo né ombra;
  - crop del volto stretto: capelli in alto, spalle tagliate in basso;
  - sottotitolo nel pannello, appena sopra la card (centro ~y 948).
- **VOLTO PIENO**: inquadratura intera, più larga. Sottotitolo sul petto (~y 1400).
- **GRAFICA PIENA**:
  - parole che entrano una alla volta, sfocate → nitide;
  - parola chiave in accento, con una sottolineatura che si disegna.

### Transizioni (misurate frame per frame)
- **Split → pieno, espansione**: ~5 frame a 30 fps, cioè **10 a 60 fps**, ease in-out.
  - Il bordo superiore della card sale da y 1010 a 0; gli angoli restano tondi fino all'ultimo frame.
  - Il crop si allarga dal volto stretto all'inquadratura intera.
  - Il pannello viene coperto e sfuma.
- **Pieno → split, collasso**: ~6 frame a 30 fps, cioè **12 a 60 fps**, ease-out (veloce all'inizio, si posa morbido). La grafica entra subito dopo, sfocata → nitida.
- **Grafica piena ↔ split / volto**: taglio secco sul beat della parola.
- **Punch-in**: dentro il volto pieno, salto di scala a ~110% su un taglio (1 frame) al cambio frase. Nasconde anche i jump-cut.
- **Ritmo**: un cambio ogni 2-4 s, mai fermi oltre ~5 s.

### Grafiche nel pannello
- Ogni grafica illustra la parola detta in quel momento, e le grafiche **si accumulano** sulla stessa scena.
  - Esempio: "3 ORE DI UTILIZZO" si rimpicciolisce in alto a sinistra e sotto entra la finestra dell'editor.
- **Entrate tipiche**:
  - blur → nitido, scale da piccolo;
  - contatore a rullo;
  - typewriter nella barra URL;
  - toggle che si spegne;
  - cursore che clicca;
  - spunte in sequenza;
  - badge "NUOVO";
  - chip che si aggiungono una alla volta.

## 2. I passi in dettaglio

| # | Script | Note |
|---|---|---|
| 1 | `transcribe.py` | `mlx_whisper` large-v3-turbo, `--word-timestamps True --condition-on-previous-text False`. Whisper **salta pezzi** (buchi di 20-60 s): le zone con voce senza parole escono come `UNCOVERED` |
| 2 | `phwords.py` | Clip corte per frase, con il prompt dei riempitivi in `reel.json` (`"Ehm... cioè, eh, ci- ci sta, mmh, insomma, no, cioè noi, noi..."`): Whisper scrive anche riempitivi e false partenze, con timestamp più precisi |
| 3 | `cut.py` | `spans`: `[id, inizio, fine, etichetta, fine forzata?]` in secondi della sorgente; le parole da scartare restano fuori. Attacco alla prima finestra ≥ -45 dB, fine RMS a -35/-32 dB, pause interne > 250 ms (< -50 dB) spezzate in pezzi, 40-50 ms di lead-in. La fine forzata serve per una parola che finisce morbida sotto -35 dB |
| 3b | verifica attacchi | Per ogni pezzo c'è il profilo RMS attorno all'attacco: se parte sulla coda di una parola scartata ("fattore…", "boh"), sposta l'inizio dello span al vero attacco |
| 4 | `voice.py` | J-cut 50 ms; coda a pieno livello fino al rumore di fondo, poi fade di 170 ms; limiter lookahead a -2 dBFS; -14 LUFS **misurati sullo stereo** (un mono duplicato legge +3 LU in ebur128) |
| 5 | `retranscribe.py` | Leggi il testo: deve scorrere senza ripetizioni. Controlla ogni `SHORT PIECE` / `LONG WORD` sulla sorgente |
| 6 | `build_cam.py` | Taglio a frame esatto con `-ss/-t` per clip, `fps=60`, concat |
| 7 | `faces.sh` | Vision di macOS con lo `swift` di sistema, su 1 frame ogni 4 a 540x960. ~7000 frame in ~20 s. Nessuna installazione: niente OpenCV/Haar |
| 8 | `plan.py` | `segments`: `[id, layout, chiave di inizio "P03.1", etichetta]`. Le parole sulla timeline sono la trascrizione del montato |
| 9 | `gfx/gen.py` | GSAP con la timeline in pausa su `window.__timelines[id]`. Libreria di camera `W` in `assets/world.js`, stile in `assets/world.css`. Tempi in secondi del segmento, presi dalle parole con `t()` |
| 10 | `render.sh` | `hyperframes@0.8.143 render --fps 240`, poi `tmix=frames=3,fps=60`: è il motion blur. Overlay `--format mov -w 1` (ProRes 4444 in streaming). `webm` con alfa = cattura PNG su disco (decine di GB), da evitare |
| 11 | `compose.py` | Vedi §3 |
| 12 | `subs.py` | Blocchi da 1-3 parole; regole in `reel.json` `subs` |
| 13 | `audio.py` | Eventi sfx dal JSON `<script id="sfx">` di ogni composizione. Riser di 2,6 s che finisce sulla giunzione del gancio. Musica dell'utente (`reel.json` `music`, vedi [musica.md](musica.md)) a -27 LUFS. Master -14 LUFS, TP ≤ -1 dBTP |
| 14 | `burn.py` | Sottotitoli e copertina disegnati con PIL, **senza browser**: robusto anche con il Mac sotto carico, quando Chrome headless va in timeout. H.264 High crf 15, AAC 320k |
| 15 | `qa.sh` | Foglio a 1 fps, foglio delle giunzioni (frame f-1 e f a ogni segmento), LUFS/TP per stem |

**Catture di pagine vere**: `node work/shoot.mjs jobs.json` (puppeteer-core + Chrome di sistema) salva il PNG e le coordinate dei testi cercati (`marks`). Consent e paywall si **nascondono via CSS, mai si accettano**. Una mark può cadere dentro un paywall coperto: controlla sempre il frame renderizzato.

**Varianti** (es. A tutta meme, B sobria): usa cartelle di render separate (`RDIR=work/rA`). Se partono con symlink ai render precedenti, fai `rm -f` della destinazione prima di scrivere (`render.sh` lo fa già), altrimenti sovrascrivi l'originale passando dal symlink.

## 3. Il compositor (`compose.py`)
```
per ogni frame f:
  gfx   → frame della grafica (taglio secco)
  split → pannello = frame della grafica; p = 0 (card chiusa).
          Se il segmento prima era cam e f-f0 < 12: p = 1 - easeOut((f-f0+1)/12)          [collasso]
  cam   → p = 1. Se il segmento prima era split e f-f0 < 10: p = easeInOut((f-f0+1)/10),
          pannello = ultimo frame della grafica precedente                              [espansione]
          punch-in 1.0 / 1.1 alternato a ogni taglio interno (se non ce ne sono: sulla pausa più lunga)
  volto: top = lerp(1010, 0, p); scala = lerp(1.05, punch, p); il punto del volto va da (540, 1480) a sé stesso
         angoli in alto r 75 finché p < 1
  overlay <id>_ov.mov (alfa) sopra il volto pieno
```
Un girato già in primo piano vuole una scala nello split di ~1.0-1.1, altrimenti la faccia non ci sta nella card.

## 4. Spec di formato
- **Formato**: 1080x1920, 60 fps, H.264, AAC 48 kHz stereo. END = ultimo frame della voce, e tutto finisce lì.
- **Stem** a durata piena: `voice`, `sfx`, `riser`, `music`.
- **Camera**:
  - glide;
  - step di 0,5 s che parte 0,25 s prima della parola;
  - push di 1,2-2 s fino a ~1,6x (mai tagliando l'informazione), poi pullback;
  - al massimo uno whip per segmento (0,45 + 0,6 s), con il whoosh a metà.
- **Profondità di campo**: card vicine sfocate a 14 px; card retrocesse a 9 px e 40% di opacità.
- **Pagine vere**: cornice fissa (raggio 36) sopra un clone sfocato. Zoom interno 1,15-1,4x; il logo del prodotto nominato compare per primo.
- **Copertina**: solo sul frame 0. Riquadro y 262-603 con bordo in gradiente.
- **Zone dei sottotitoli**: split y ~948 · volto e grafica y ~1400. Niente testo sotto i 30 px.
- **Livelli sfx** rispetto al picco della voce:
  - click e pop -10 dB, whoosh -9 dB, tasti -16 dB;
  - campione dei soldi -3 dB;
  - riser 14 dB sotto il picco.
- **Report** in `edit/report.md`:
  - END;
  - tabella dei segmenti;
  - take scelti;
  - grafiche e fatti verificati con le fonti;
  - LUFS/TP per traccia;
  - cosa non è stato fatto e cosa è stato fatto al suo posto.

## 5. Gotcha
- **`while read` + ffmpeg/npx**: metti sempre `-nostdin` o `< /dev/null`, altrimenti il loop si ferma dopo il primo giro.
- **Filtri GSAP**: un `filter` interpolato partendo da `none` scatta. Serve un filtro base esplicito in CSS.
- **Maschera dello split**: va su un wrapper **non** trasformato (`.world-mask`), altrimenti si muove con la camera.
- **Disco**: cancella il 240 fps dopo il tmix.
- **Versione fissa**: `npx hyperframes` senza versione scarica sempre l'ultima. Fissala (`hyperframes@0.8.143`).
- **Out-of-memory a 240 fps** (es. emoji grandi):
  - `NODE_OPTIONS=--max-old-space-size=12288` (già in `render.sh`) e meno worker;
  - con 3 render da 8 worker in parallelo, i segmenti pesanti falliscono con "Navigation timeout": rilanciali da soli.
- **Lavori indipendenti**: render di segmenti diversi, varianti, QA si lanciano come processi paralleli in background, max 2-3 render HyperFrames insieme. Il collo di bottiglia è CPU/RAM, non serve un agente per ogni render.
- **`remove-background` di HyperFrames**: prende anche mensole e pareti, va pulito. Comunque niente testa scontornata.
- **HyperFrames Studio** (`hyperframes preview`):
  - modifica i file aggiungendo `data-hf-id`;
  - copia la cartella prima, o pulisci dopo con `sed -E 's/ data-hf-id="[^"]*"//g'`;
  - usa `--port` se la 3002 è occupata;
  - mostra una scena alla volta.
- **Render lunghi**: tieni sveglio il Mac.
- **Cambio di span = catena intera**: `cut.py` → `voice.py` → `build_cam.py` → `faces.sh` → `plan.py` → `subs.py` → `compose.py`. Se salti `build_cam.py` e `faces.sh`, dal primo taglio cambiato in poi il volto resta indietro (o avanti) rispetto alla voce, fino alla fine. `compose.py` controlla date e numero di frame e si ferma.
