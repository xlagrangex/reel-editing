---
name: reel-editing
description: Da usare quando bisogna montare un reel verticale 9:16 a partire da un girato parlato (talking head) interamente in codice, con ffmpeg, Python e HyperFrames/GSAP, invece che in un editor. Trigger tipici sono "monta questo reel", "edita il video", "fai il reel dal girato", "togli le balbuzie e metti le grafiche", Instagram Reels, TikTok, YouTube Shorts.
---

# Reel editing in codice

Ogni taglio, grafica, sottotitolo e suono è un file che si rigenera. Il pezzo difficile non è la tecnica ma il gusto: le grafiche devono fare il **direttore creativo**, non il trascrittore del parlato.

Prima di montare leggi:
- [references/gusti.md](references/gusti.md): le regole emerse da sei round di feedback reali, cioè cosa piace e cosa è cringe;
- [references/procedura.md](references/procedura.md): i dettagli tecnici di ogni passo e le misure della reference.

## Prima di tutto
1. **Reference**: se l'utente ha un video di riferimento, scegline **uno** ed estrai **tutti** i frame in fogli 10x6. Misura layout, raggi, durate delle transizioni in frame ed easing prima di scrivere codice.
2. **Spec incollata = autonomia totale**: niente domande dopo. Se invece manca un'informazione, segnala il buco e chiedi una cosa sola, quando serve.
3. **Installazioni solo in locale** (`.venv`, `node_modules` del progetto), mai a livello di sistema. Se un'installazione viene rifiutata, non riprovarla.
4. **Musica**: la traccia è dell'utente. La skill non ha un sottofondo di default, altrimenti tutti i reel suonerebbero uguali. Se l'utente non ce l'ha, deve generarla lui: spiegagli come con [references/musica.md](references/musica.md) e intanto monta senza.
5. **Requisiti**: macOS su Apple Silicon (mlx-whisper; Vision per il face tracking, con lo `swift` di sistema), ffmpeg, Node 18+, Python 3.11+. Chrome serve solo per le catture di pagine, `yt-dlp` solo per i suoni veri.

## Avvio
```bash
zsh <cartella della skill>/templates/nuovo-reel.sh ~/reel/nome-reel ~/Downloads/girato.MOV
```
Copia il template, scrive il percorso del girato in `reel.json` e stampa i comandi d'installazione locale. Tutta la configurazione del reel vive in `reel.json`: girato, prompt delle balbuzie, copertina, span di taglio, segmenti, sottotitoli, musica.

## Pipeline
Si lancia tutto dalla radice del progetto con `.venv/bin/python` (o `zsh` per gli script `.sh`).

| # | Comando | Cosa controllare |
|---|---|---|
| 1 | `work/transcribe.py` | Le righe `UNCOVERED`: Whisper salta pezzi interi, vanno ritrascritti con il passo 2 |
| 2 | `work/phwords.py ID:inizio-fine …` | Riempitivi, false partenze e ripetizioni con i loro tempi: restano **fuori** dagli span |
| 3 | `work/cut.py` | Gli span vengono da `reel.json` `spans`. Per ogni attacco c'è il profilo RMS: non deve partire sulla coda di una parola scartata. Se cambi gli span, rifai **tutti** i passi da 4 a 8: `compose.py` si ferma se camera o tracking sono rimasti indietro |
| 4 | `work/voice.py` | Voce a -14 LUFS, J-cut di 50 ms |
| 5 | `work/retranscribe.py` | Rileggi **tutto** il testo del montato. Le righe `SHORT PIECE` e `LONG WORD` sono ripetizioni che Whisper ha collassato |
| 6 | `work/build_cam.py` | Camera con tagli a frame esatto |
| 7 | `work/faces.sh` | Faccia trovata in quasi tutti i campioni |
| 8 | `work/plan.py` | I segmenti vengono da `reel.json` `segments`; correggi le righe `WARN` |
| 9 | `gfx/gen.py` | Riempi `SCENES`. Ogni segmento senza scena ha un segnaposto: rimpiazzali tutti |
| 10 | `work/render.sh [id…]` | Il foglio `work/r/<id>_sheet.jpg` di ogni grafica |
| 11 | `work/compose.py` | `work/base.mp4`: layout e transizioni a card |
| 12 | `work/subs.py` | Blocchi ed evidenziazioni (regole in `reel.json` `subs`) |
| 13 | `work/audio.py` | Le righe `WARN`: un suono mancante resta silenzio, e senza `music` in `reel.json` il reel non ha sottofondo |
| 14 | `work/burn.py` | `edit/final.mp4` con sottotitoli, copertina e master audio |
| 15 | `work/qa.sh` | Foglio a 1 fps, foglio delle giunzioni, LUFS/TP di ogni stem. Poi i frame **interi** all'inizio e alla fine di ogni push |

Dopo una modifica alle grafiche o a `reel.json`, `zsh work/build.sh [id…]` rifà i passi 9-15.

Prima del passo 9 scrivi un **trattamento**: una tabella con tempo, cosa dice, riferimento visivo e animazione. Ogni grafica deve cadere sulla parola: `t("S03", "milioni")` dà il tempo della parola dentro il segmento.

## Quick reference
- **Layout**:
  - `split`: pannello grafico in y 40-900, card del volto a tutta larghezza da y 1010, angoli in alto r 75;
  - `cam`: volto pieno, con overlay leggeri ammessi;
  - `gfx`: grafica piena, contenuto fino a y ~1300 e sottotitoli a y 1400.
- **Transizioni**:
  - split → cam: la card si espande in 10 frame, ease in-out;
  - cam → split: collasso in 12 frame, ease-out;
  - grafica: taglio secco;
  - dentro `cam`: punch-in 1.0/1.1 a ogni jump-cut.
- **Ritmo**: un cambio ogni 2-4 s, mai più di ~8 s per segmento, mai lo stesso layout due volte di fila. Si apre in split e si chiude sul volto.
- **Camera** (`W` in `gfx/assets/world.js`):
  - `frame(cx, cy, s, ax, ay)`, `step`, `push`, `pull`, `glide`, `whip` (uno per segmento);
  - `focus` / `demote`, `land`;
  - `type`, `count`;
  - `capture` (pagina vera con `move` / `mark`);
  - `gif` (sprite sheet).
- **Scene pronte in `gen.py`**:
  - `domande`: card che si accumulano;
  - `numero`: le cifre girano come rulli e si fermano sulla parola;
  - `chip`: overlay sul volto pieno;
  - `kinetic`: segnaposto;
  - `capture_block`, `tex` / `svg`: equazioni intere in LaTeX.
- **Render**: 240 fps, poi `tmix` a 60 fps (motion blur vero). Gli overlay vanno in ProRes 4444 con alfa. Al massimo 2-3 render in parallelo.
- **Audio**: master -14 LUFS, TP ≤ -1 dBTP; la musica dell'utente a -27 LUFS sotto la voce.

## Le regole che pesano di più
1. **Mai la testa scontornata** che esce dalla card. Il corpo intero scontornato con uno sfondo dietro va bene, ogni tanto.
2. **Ogni grafica si capisce al volo**: oggetti riconoscibili, non astrazioni. Il letterale va bene solo in alcuni punti; altrove serve un **riferimento esterno preciso** (fatto storico, logo vero, immagine vera, cultura pop). Il riferimento però deve spiegarsi da solo nel contesto: se per capirlo serve una frase che il creator non dice, si torna al letterale. Esempio bocciato: Oppenheimer su "l'azienda che avverte dei rischi è quella che costruisce l'AI".
3. **Un numero forte detto a voce è un momento visivo**: zoom o "jackpot" sul numero stesso, sincronizzato alla parola. Mai slot machine o la scritta "JACKPOT".
4. **Un push non taglia mai l'informazione**: controlla il frame intero a inizio e fine.
5. **Pochi suoni, ma veri**: un suono riconoscibile si prende vero (`work/grab_sfx.sh`), non si rifà in sintesi. Dove il suono non è deciso, silenzio. Per i soldi, la notifica di vendita di Shopify, già inclusa in `sfx/soldi.wav`.
6. **Sottotitoli sul volto**: ombra morbida ma evidente, mai contorno nero.
7. **Zero balbuzie, zero passaggi di senso persi**: si rilegge il montato, non solo i tagli. Sono ripetizioni anche i **doppioni di concetto** detti con parole diverse a pochi secondi di distanza ("tutte le aziende AI, americane e cinesi", poi "chiede di rallentare a OpenAI e alle aziende cinesi"): se ne tiene uno, di solito il più concreto.
8. **Fatti**:
   - quelli esterni si verificano e si citano;
   - i numeri sull'attività del creator sono suoi, mai cercati fuori;
   - una stima si chiama "stima".
9. **Chiusura**: una frase semplice ("fammi sapere cosa ne pensi"), niente card CTA elaborata.

## Errori comuni
| Sintomo | Causa e rimedio |
|---|---|
| Una ripetizione resta nel montato | Whisper collassa le ripetizioni identiche: segui i flag del passo 5 e ritrascrivi la **sorgente** attorno al pezzo |
| `JavaScript heap out of memory` o `Navigation timeout of 60000 ms` | Troppi render insieme: rilancia quel segmento da solo, con `WORKERS=4` |
| Lo Studio di HyperFrames ha rotto il generatore | `hyperframes preview` aggiunge `data-hf-id` ai file. Pulisci con `sed -E 's/ data-hf-id="[^"]*"//g'`, usa `--port` e chiudilo quando non serve. Lo Studio mostra una scena alla volta: il reel intero esiste solo come `edit/final.mp4` |
| L'evidenziazione su una pagina catturata è vuota | La mark cade sotto un paywall nascosto: guarda il frame renderizzato |
| Un oggetto compare prima del suo momento (monete fuori campo che fanno ombra sul bordo, scintille già visibili) | Un `fromTo` con `opacity: 1` nello stato iniziale lo applica dal frame 0 (`immediateRender`). Su ogni `fromTo` che parte dopo lo 0 aggiungi `immediateRender: false` |
| Un segmento grafico parte su un fondo bianco vuoto | Dopo un taglio secco, 0,3-0,5 s di vuoto si vedono come un lampo: il contenuto deve comparire entro ~0,1 s. Un numero che si ferma sulla parola può entrare già in rotazione |
| Da un certo punto in poi il volto è fuori sync con la voce, fino alla fine | Hai cambiato gli span e rifatto voce e sottotitoli, ma non `work/cam.mp4` (`build_cam.py`) né il tracking (`faces.sh`). Rifalli, poi `compose.py`. Il QA del sync confronta immagine e voce (una vocale aperta vicino alla fine, contro il frame sorgente della stessa parola), non voce contro voce |
| GSAP scatta sui filtri | Filtro base esplicito in CSS (`blur(0px) brightness(1)`), mai interpolare da `none` |
| L'utente indica un suono "al secondo X" che lì non c'è | I timestamp a orecchio sbagliano di 1-2 s: elenca gli eventi (`edit/stems/sfx_events.json`), misura l'RMS di ogni stem nella finestra e prendi quello che si sente davvero |
| Il loop di shell si ferma dopo il primo giro | ffmpeg/npx dentro un `while read`: aggiungi `-nostdin` / `< /dev/null` |
| I job si fermano di notte | Tieni sveglio il Mac durante i render lunghi |

## Stile
Tema di default: bianco + blu.
- Fondo bianco, inchiostro blu notte `#0c1f3f`.
- Font **Plus Jakarta Sans** 800 (licenza OFL, incluso).
- Gradiente `#0a3fd6 → #1b74ff → #2aa9f5` a 135° su parole chiave, contatori, bordo della copertina.

Si cambia in due punti, i token di `gfx/assets/world.css` e le costanti in cima a `work/burn.py`. I raggi restano: card 32, tile 72, doc 40, cornice delle catture 36, copertina 30. Dettagli in [references/stile.md](references/stile.md).
