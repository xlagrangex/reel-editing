# Gusti: cosa funziona e cosa è cringe

Queste regole vengono da sei round di feedback reali su un reel montato in codice, ognuno con una versione completa rivista dal creator. Valgono per tutti i reel, salvo che l'utente chieda diversamente. Gli esempi sono quelli che le hanno fatte nascere.

## Taglio e contenuto
- **Balbuzie: vanno trovate tutte**: false partenze ("ma più che altro perché, cioè…"), riempitivi ("boh"), frasi ripetute. Il solo taglio sui silenzi non basta: servono le trascrizioni corte con il prompt dei riempitivi (`phwords.py`).
- **Mai tagliare un passaggio di senso**. Confronta il testo del montato con l'intero girato: Whisper ha buchi, e il creator si accorge di ogni frase sparita.
- **Whisper collassa le ripetizioni identiche**: "ma hey… ma hey" esce una volta sola, anche con il prompt. Ogni pezzo corto (< 1,2 s) o parola lunga (> 0,8 s) si ricontrolla sulla sorgente.
- **Chiusura**: una frase semplice ("fammi sapere cosa ne pensi"), niente card CTA elaborata.
- **Fatti e numeri**:
  - i numeri sull'attività del creator sono suoi, non vanno cercati fuori;
  - i fatti esterni si verificano e si citano;
  - una stima si scrive "stima".
  - Se il creator sbaglia un fatto a voce (dice "8 problemi del Millennio" ma sono 7), la grafica mostra quello giusto e lo si segnala.

## Volto e layout
- **Mai la testa scontornata** che esce sopra la card. Il corpo intero scontornato con uno sfondo dietro va bene, ogni tanto.
- **Transizioni come la reference**:
  - split → volto: la card si espande, ~10 frame a 60 fps, ease in-out;
  - volto → split: collasso, ~12 frame, ease-out;
  - grafiche: tagli secchi;
  - punch-in ~110% sui cambi frase.
- **Volto pieno non vuol dire niente grafica**. Sul volto pieno vanno anche overlay leggeri: chip, sticker, lo screenshot della pagina citata. Non occupano mezzo schermo, lasciano libera la faccia e sono il terzo tipo di scena accanto a split e grafica piena.
- **Arrotondamenti fissi**: card 32, tile 72, doc 40, cornice delle catture 36, copertina 30. Un cambio di stile cambia i colori, non i raggi.

## Grafiche: fare il direttore creativo
- **Il difetto da evitare** sono le grafiche che ripetono alla lettera il parlato. Il letterale va bene **in alcuni punti** (numeri, nomi, la pagina citata, un "≠"), ma non può essere l'unico registro.
- **Per ogni passaggio** chiediti se c'è un **riferimento esterno preciso** che commenta, rilancia o rende ironico quello che dice: fatti storici, cultura pop, oggetti riconoscibili, loghi veri dei prodotti, immagini vere. Esempio: la turbolenza fotografata dalla NASA per Navier-Stokes.
- **Prima un trattamento scritto**: una tabella con tempo, cosa dice, riferimento e animazione. Poi il codice.
- **Ogni grafica si capisce al volo**. Le astrazioni (pezzi che si assemblano, curve generiche) non funzionano; gli oggetti riconoscibili sì (persone → freccia "costruito" → AI).
- **Un esempio solo per concetto**. Un secondo esempio (Kasparov contro Deep Blue) confonde: la gente deve seguire due storie. Meglio un'animazione astratta ma con personalità, come una faccia "Noi" che se la prende, con uno zoom drammatico.
- **Info mostrata ≤ info detta**: un oggetto riconoscibile, non tre. Per "20 anni" basta la finestra di copia di Windows con la stima del tempo che cresce, senza barre e confronti attorno.
- **Niente timeline piene di testo**: in un reel non si leggono. Al loro posto un'idea sola, visiva.
- **Le grafiche si accumulano** sulla stessa scena invece di cambiare scena a ogni parola.
- **Quando nomini un'azienda o una pagina**, mostra lo screenshot vero della pagina, anche in un overlay piccolo.
- **Personaggi storici con l'immagine vera e dettagliata** (il dipinto di Archimede di Domenico Fetti), non uno sticker o un'emoji.
- **Equazioni per intero**, renderizzate in LaTeX (`tex()` in `gen.py`). Mai una forma abbreviata.
- **Etichette ovvie: via**:
  - niente intestazioni che dicono cos'è l'oggetto ("SCONTRINO" sopra uno scontrino);
  - niente credit sotto le opere d'arte.
  - Un'emoji accanto alla voce concreta invece sì (🥜 vicino a "Noccioline").
- **Folle e moltiplicazioni** ("10.000 agenti"): non disegnare 10.000 elementi, perché sotto i ~15 px diventano una texture grigia. Disegnane al massimo ~700-1.600 e lascia che sia il **contatore** a dire 10.000.
- **Immagini esterne**: solo in pubblico dominio o con licenza libera (Wikimedia Commons, NASA).
- **Quando rifai un segmento**, ripassa le versioni precedenti e tieni i movimenti che erano piaciuti.

## Numeri e soldi
- **Un numero forte detto a voce** ("30 milioni") merita un momento visivo vero, sincronizzato alla parola: push sul numero oppure "jackpot sul numero stesso". Nel jackpot le cifre girano come rulli, si fermano una alla volta, poi arrivano gradiente e raggi (`numero()` in `gen.py`).
- **Cringe, mai**:
  - slot machine disegnata, la parola "JACKPOT", ciliegie;
  - "OBIEZIONE!" alla Ace Attorney;
  - "Chi vuol essere milionario".
- **I soldi si sentono**: per il suono vale la regola dei suoni qui sotto. Niente icone di monete disegnate male.

## Camera e zoom
- **Un push non taglia mai l'informazione**: dopo il push si deve ancora leggere tutto. Controlla il frame intero all'inizio e alla fine: l'oggetto inquadrato è centrato e sta tutto nei 1080 px.
- **Le interfacce piccole sul telefono non si leggono** (una finestra di dialogo, un'app). La camera va sulla riga che conta e la tiene in grande mentre i valori cambiano, spinge sul valore detto, poi torna a 1x per il finale.

## Meme
- **Al massimo 1-2 meme in tutto il video**, salvo che l'utente chieda la versione "tutta meme". Se è indeciso, proponi due varianti: una piena di meme e una sobria.
- **Le scene demenziali piacciono**, anche estreme: l'AI che conta tre R in "strawberry" e risponde "2", con la Math Lady e 🤡.
- **GIF meme famose** (Math Lady, il brindisi di Gatsby): si scaricano come mp4 e si convertono in sprite sheet (`work/gif2sprite.sh`), così il render è deterministico. Vanno su card piccole, mai sopra la faccia.

## Suoni
- **Meno suoni, ma veri**. Rifatti in sintesi, i suoni meme sono risultati cringe. In ordine di peggio:
  - air horn;
  - finestra di Windows (ding, blip, errore);
  - scontrino (stampante + cassa);
  - chime sui pop-up;
  - power-up;
  - buzz;
  - popper.
- **Un suono riconoscibile si prende vero**, da una fonte reale (`work/grab_sfx.sh`): prima occorrenza pulita, verificata su un secondo upload indipendente. I siti con il CAPTCHA di Cloudflare non si superano: si cerca un'altra fonte. Verifica di poter usare il suono.
- **Soldi = la notifica di vendita di Shopify** ("cha-ching"), messa in `sfx/soldi.wav`. Non una cassa generica.
- **Dove il suono non è stato deciso: silenzio**. Niente suono inventato al suo posto.
- **Restano in sintesi** solo i suoni d'interfaccia discreti: click, pop, whoosh a metà di uno whip, tasti, tick, rulli che si fermano.
- **Musica**: -27 LUFS sotto la voce. Se l'utente dà una traccia, sostituisce il letto sintetizzato e chiude con un fade-out.

## Sottotitoli
- **Sul volto**: bianchi con un'ombra morbida ma evidente, **mai un contorno nero**, soprattutto sulle parole evidenziate. Sulle parole in gradiente al massimo un bordino bianco sottile.
- **Sul pannello e sulle grafiche**: inchiostro scuro. Quando una grafica è su una foto, si passa allo stile "su volto" con `DARK=S04` o `DARK=S04@5.0` in `burn.py`, cioè solo per i primi 5 s del segmento.
- **Blocchi da 1-3 parole**. Le evidenziazioni sono più grandi e in gradiente: ogni 2-3 blocchi, mai due di fila.
