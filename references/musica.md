# Musica: generala tu

La skill **non ha un sottofondo di default**, ed è voluto: se ce l'avesse, tutti i reel montati con questa skill avrebbero la stessa musica. Ogni creator usa una traccia sua, generata o con licenza. Se `reel.json` non ne indica una, `audio.py` monta senza musica e lo segnala con un `WARN`.

## Com'è fatta una buona traccia di sottofondo
- **Strumentale**, senza voce.
- **Durata**: almeno quella del reel più 5 s (`END_s` in `work/plan.json`). Meglio 2-3 minuti, così va bene per più reel. Se è più corta, `audio.py` lo segnala.
- **Tempo costante**, 100-120 BPM, senza drop né cambi di tempo.
- **Niente melodia protagonista nella zona della voce** (circa 200 Hz-3 kHz): pad, basso morbido, ritmica leggera. Deve sostenere, non farsi notare.
- **Formato**: mp3, wav o m4a, quello che c'è. La legge ffmpeg.

## Come generarla
1. **Scegli un generatore musicale AI**, per esempio Suno, Udio, ElevenLabs Music o Stable Audio. Controlla che il piano che usi permetta l'uso commerciale sui social: con i piani gratuiti spesso non è permesso.
2. **Imposta la modalità strumentale** e parti da questo prompt (in inglese rende meglio):
   ```
   instrumental background music for a talking-head social video, no vocals,
   warm minimal electronic, 110 BPM, soft kick, mellow pads, round bass,
   no drops, no lead melody, steady low energy, 2 minutes
   ```
   Cambia lo stile per dare al creator un suono riconoscibile e suo:
   - `lo-fi hip hop, dusty drums, soft rhodes`;
   - `acoustic, fingerpicked guitar, light percussion`;
   - `modern tech, plucks, light arpeggio, clean`;
   - `cinematic but restrained, soft piano, no build-ups`.
3. **Genera 3-4 versioni** e ascoltale **sotto la voce**, non da sole. Tieni quella che non si nota.
4. **Salvala** in `music/` dentro il progetto e scrivi in `reel.json` `"music": "music/base.mp3"`. Per una prova al volo puoi anche usare `MUSIC=<file>`.
5. **Livello**: `audio.py` la porta a -27 LUFS sotto la voce e la chiude con un fade-out di 1,2 s. Se in qualche punto copre la voce, scegli un'altra versione o abbassa il -27 dentro `audio.py`, per esempio a -29.

Una traccia per creator, riusata su tutti i suoi reel, va benissimo: diventa parte del suo stile. Un brano preso da una libreria royalty-free è legale, ma non è unico, perché lo usano anche altri.

## Per l'agente
- **Se l'utente non ha una traccia**: non inventarne una in sintesi e non riusare la musica di un altro progetto. Spiegagli i passi qui sopra, con il prompt già adattato al tono del suo reel, e intanto monta senza musica.
- **Se nella sessione c'è uno strumento di generazione musicale**, puoi generarla tu con lo stesso prompt, ma solo dopo l'ok dell'utente: di solito costa crediti.
