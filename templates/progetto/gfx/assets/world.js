// Shared camera grammar for every segment. All times are in segment seconds.
(function () {
  const W = {};
  W.tl = null;
  W.init = function (id) {
    const tl = gsap.timeline({ paused: true });
    window.__timelines = window.__timelines || {};
    window.__timelines[id] = tl;
    W.tl = tl;
    return tl;
  };

  // camera frames a world point (cx, cy) at a given scale: the point lands on the
  // screen anchor (ax, ay), default the visual centre of the content zone.
  W.frame = function (cx, cy, s, ax, ay) {
    ax = ax === undefined ? 540 : ax;
    ay = ay === undefined ? 700 : ay;
    return { x: ax - 540 - (cx - 540) * s, y: ay - 700 - (cy - 700) * s, scale: s };
  };
  W.set = function (f) { gsap.set("#world", f); };
  W.glide = function (f, at, dur) { W.tl.to("#world", Object.assign({ duration: dur, ease: "sine.inOut" }, f), at); };
  // a step to the next element starts 0.25s before the word that names it
  W.step = function (f, wordAt) { W.tl.to("#world", Object.assign({ duration: 0.5, ease: "power3.inOut" }, f), Math.max(0, wordAt - 0.25)); };
  W.push = function (f, at, dur) { W.tl.to("#world", Object.assign({ duration: dur || 1.6, ease: "power2.inOut" }, f), at); };
  W.pull = function (f, at, dur) { W.tl.to("#world", Object.assign({ duration: dur || 1.4, ease: "power2.inOut" }, f), at); };
  // one whip per segment at most: fast out to an offset, then in to the new framing
  W.whip = function (fOut, fIn, at) {
    W.tl.to("#world", Object.assign({ duration: 0.45, ease: "power3.in" }, fOut), at);
    W.tl.to("#world", Object.assign({ duration: 0.6, ease: "power3.out" }, fIn), at + 0.45);
    return at + 0.45; // mid-whip time for the whoosh
  };

  // depth of field: the read card is sharp, neighbours blur and dim
  W.focus = function (sel, others, at, dur) {
    dur = dur || 0.8;
    W.tl.to(sel, { filter: "blur(0px) brightness(1)", opacity: 1, duration: dur, ease: "power2.inOut" }, at);
    if (others) W.tl.to(others, { filter: "blur(14px) brightness(0.7)", duration: dur, ease: "power2.inOut" }, at);
  };
  W.demote = function (sel, at, dur) {
    W.tl.to(sel, { filter: "blur(9px) brightness(1)", opacity: 0.4, duration: dur || 0.7, ease: "power2.inOut" }, at);
  };

  // a card lands: fade + rise + slight scale, settles on its final state
  W.land = function (sel, at, opts) {
    opts = opts || {};
    W.tl.fromTo(sel, { opacity: 0, y: opts.dy === undefined ? 60 : opts.dy, scale: opts.s0 || 0.94 },
      { opacity: 1, y: 0, scale: 1, duration: opts.dur || 0.55, ease: "power3.out" }, at);
  };

  // typing: deterministic, driven by the timeline playhead
  W.type = function (el, text, at, cps, caret) {
    el = typeof el === "string" ? document.querySelector(el) : el;
    const o = { n: 0 };
    el.textContent = "";
    const dur = text.length / (cps || 18);
    W.tl.to(o, {
      n: text.length, duration: dur, ease: "none",
      onUpdate: function () { el.textContent = text.slice(0, Math.round(o.n)); },
    }, at);
    W.tl.set(o, { n: 0, onComplete: null }, 0);
    return at + dur;
  };

  // counting number with a formatter
  W.count = function (el, from, to, at, dur, fmt) {
    el = typeof el === "string" ? document.querySelector(el) : el;
    fmt = fmt || function (v) { return Math.round(v).toLocaleString("it-IT"); };
    const o = { v: from };
    el.textContent = fmt(from);
    W.tl.to(o, { v: to, duration: dur, ease: "power2.out", onUpdate: function () { el.textContent = fmt(o.v); } }, at);
  };

  // A real page capture in a fixed frame. cssW = page width in CSS px.
  // Returns a framing function: view(cx, cy, zoom) -> transform for the image so the
  // CSS point (cx, cy) sits in the centre of the frame at `zoom` (1 = page fits width).
  W.capture = function (root, opts) {
    root = typeof root === "string" ? document.querySelector(root) : root;
    const fw = opts.w, fh = opts.h, cssW = opts.cssW;
    const base = fw / cssW;
    const frame = root.querySelector(".cap-frame");
    const page = root.querySelector(".cap-page");
    const bed = root.querySelector(".cap-bed .cap-page-bed");
    frame.style.left = opts.x + "px"; frame.style.top = opts.y + "px";
    frame.style.width = fw + "px"; frame.style.height = fh + "px";
    page.style.width = cssW + "px";
    if (bed) bed.style.width = cssW + "px";
    function view(cx, cy, zoom) {
      const s = base * (zoom || 1);
      return { x: fw / 2 - cx * s, y: fh / 2 - cy * s, scale: s };
    }
    function bedView(v) {
      // the clone is 1.6x bigger and follows the same motion, centred on the frame
      const k = 1.6;
      return { x: opts.x + v.x * k - (fw * (k - 1)) / 2 + 80, y: opts.y + v.y * k - (fh * (k - 1)) / 2 + 80, scale: v.scale * k };
    }
    const api = {
      view: view,
      set: function (cx, cy, zoom) { const v = view(cx, cy, zoom); gsap.set(page, v); if (bed) gsap.set(bed, bedView(v)); },
      move: function (cx, cy, zoom, at, dur) {
        const v = view(cx, cy, zoom);
        W.tl.to(page, Object.assign({ duration: dur || 0.6, ease: "power2.inOut" }, v), at);
        if (bed) W.tl.to(bed, Object.assign({ duration: dur || 0.6, ease: "power2.inOut" }, bedView(v)), at);
      },
      // highlight a mark rect (CSS px) drawing from the left
      mark: function (m, at, pad) {
        pad = pad || 6;
        const el = document.createElement("div");
        el.className = "cap-hl";
        Object.assign(el.style, { left: m.x - pad + "px", top: m.y - pad + "px", width: m.w + pad * 2 + "px", height: m.h + pad * 2 + "px", transformOrigin: "0 50%" });
        page.appendChild(el);
        W.tl.fromTo(el, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 0.45, ease: "power2.out" }, at);
        return el;
      },
    };
    return api;
  };

  // a GIF as a sprite sheet (cols per row, n frames of fw x fh), stepped by the timeline: deterministic frames.
  // Make the sheet with work/gif2sprite.sh; put it on a small card, never over the face.
  W.gif = function (sel, cols, n, fps, fw, fh, at, dur, off) {
    const el = document.querySelector(sel), o = { t: 0 };
    const show = function () {
      const k = Math.floor((o.t + (off || 0)) * fps) % n;
      el.style.backgroundPosition = (-(k % cols) * fw) + "px " + (-Math.floor(k / cols) * fh) + "px";
    };
    show();
    W.tl.to(o, { t: dur, duration: dur, ease: "none", onUpdate: show }, at);
  };

  window.W = W;
})();
