# reel-editing

Una **skill per [Claude Code](https://claude.com/claude-code)** che monta un reel verticale 9:16 a partire da un girato parlato (talking head), **interamente in codice**: ffmpeg, Python e [HyperFrames](https://github.com/heygen-com/hyperframes)/GSAP. Niente timeline da trascinare: ogni taglio, grafica, sottotitolo e suono è un file che si rigenera.

![anteprima](docs/anteprima.jpg)

```
girato ──► trascrizione parola per parola ──► caccia alle balbuzie ──► taglio + voce a -14 LUFS
       ──► piano dei segmenti (split / volto / grafica) ──► grafiche animate sulle parole
       ──► compositor con transizioni a card ──► sottotitoli + suoni + master ──► final.mp4 + QA
```

## Cosa fa
- **Taglia le balbuzie**: false partenze, riempitivi, frasi ripetute. Whisper viene usato due volte: prima sul girato, con un prompt pieno di "ehm, cioè"; poi sul montato, per controllare che non resti nulla e che non manchi nessun passaggio di senso.
- **Alterna tre layout**:
  - split: grafica in alto, card del volto in basso con gli angoli tondi;
  - volto pieno, con overlay leggeri;
  - grafica piena.
  - La card si espande in 10 frame e collassa in 12, con punch-in sui jump-cut. Le misure sono prese frame per frame da una reference.
- **Anima le grafiche sulle parole**: ogni animazione cade sul tempo della parola detta. La libreria di camera ha push, step, whip, profondità di campo, catture di pagine vere con evidenziazione, contatori, GIF deterministiche ed equazioni in LaTeX.
- **Sottotitoli**: blocchi da 1-3 parole con parole chiave in gradiente e un'ombra morbida sul volto (mai contorno nero). Più una copertina sul primo frame.
- **Audio**: pochi suoni discreti, i campioni veri dove serve un suono riconoscibile (il "cha-ching" di Shopify per i soldi è già incluso), un riser sul gancio e la musica a -27 LUFS sotto la voce. Master a -14 LUFS e true peak ≤ -1 dBTP.
- **QA**: foglio a 1 fps, foglio delle giunzioni, loudness di ogni traccia.

La parte che conta di più non è tecnica: [`references/gusti.md`](references/gusti.md) raccoglie le regole emerse da sei round di feedback reali, cioè cosa funziona e cosa è cringe in un reel di questo tipo.

## Installazione (come skill di Claude Code)
```bash
git clone https://github.com/xlagrangex/reel-editing.git ~/.claude/skills/reel-editing
```

Poi, in Claude Code, invoca `/reel-editing`, oppure di' semplicemente *"monta questo reel"* indicando il file del girato.

Per partire a mano:
```bash
zsh ~/.claude/skills/reel-editing/templates/nuovo-reel.sh ~/reel/primo-reel ~/Downloads/girato.MOV
```

## Requisiti
- macOS su **Apple Silicon**: la trascrizione usa `mlx-whisper`, il face tracking usa Vision con lo `swift` di sistema.
- `ffmpeg`, Node 18+, Python 3.11+.
- Google Chrome, solo per le catture di pagine web.
- `yt-dlp`, solo per prendere suoni veri.

Le dipendenze Python e Node si installano **dentro il progetto del reel** (`.venv`, `node_modules`), mai a livello di sistema: i comandi li stampa `nuovo-reel.sh`.

## Musica: generala tu
La skill **non include un sottofondo**, ed è voluto: altrimenti chiunque la usi avrebbe la stessa musica. Genera una traccia tua con un generatore musicale AI (Suno, Udio, ElevenLabs Music, Stable Audio…), controllando che il tuo piano permetta l'uso commerciale. Salvala nel progetto e indicala in `reel.json`:

```json
"music": "music/base.mp3"
```

Il prompt di partenza, le caratteristiche che deve avere la traccia (strumentale, 100-120 BPM, niente melodia sopra la voce) e come sceglierla sono in [`references/musica.md`](references/musica.md).

## Struttura
| Percorso | Cosa contiene |
|---|---|
| `SKILL.md` | le istruzioni per l'agente: pipeline, quick reference, regole, errori comuni |
| `references/gusti.md` | il gusto: grafiche da direttore creativo, numeri, suoni, sottotitoli, meme |
| `references/procedura.md` | i dettagli tecnici di ogni passo, le misure della reference, i gotcha |
| `references/stile.md` | il tema bianco + blu e come cambiarlo |
| `references/musica.md` | come generare la propria musica di sottofondo |
| `templates/nuovo-reel.sh` | crea un nuovo progetto di reel dal template |
| `templates/progetto/` | il template: `reel.json`, gli script in `work/`, le grafiche in `gfx/` |

## Stile
Il tema di default è bianco + blu: fondo bianco, inchiostro blu notte, font **Plus Jakarta Sans** e gradiente blu → azzurro. Si cambia in due file, vedi [`references/stile.md`](references/stile.md).

## Licenza
Codice e documentazione: [MIT](LICENSE). Il font Plus Jakarta Sans è incluso sotto [SIL Open Font License 1.1](templates/progetto/gfx/assets/fonts/OFL.txt). I suoni e le immagini che scarichi per i tuoi reel restano soggetti alle loro licenze: verifica di poterli usare.
