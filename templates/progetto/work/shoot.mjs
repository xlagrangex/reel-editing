import puppeteer from 'puppeteer-core';
import fs from 'fs';
const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
// Real page captures for W.capture(): usage `node work/shoot.mjs jobs.json` with [{name, url, marks: ["text to find"], width, maxH}].
// Consent banners and paywalls are HIDDEN via CSS, never accepted. Marks can land under a hidden paywall: check the render.
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
fs.mkdirSync('gfx/assets/cap', { recursive: true });
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--hide-scrollbars', '--lang=en-US'] });
const out = {};
for (const j of jobs) {
  const page = await browser.newPage();
  await page.setViewport({ width: j.width || 1100, height: j.height || 1400, deviceScaleFactor: 2 });
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36');
  try { await page.goto(j.url, { waitUntil: 'networkidle2', timeout: 60000 }); } catch (e) { console.error(j.name, 'goto', e.message); }
  await new Promise(r => setTimeout(r, 2500));
  await page.evaluate(() => {
    const kill = ['[id*="consent" i]','[class*="consent" i]','[id*="cookie" i]','[class*="cookie" i]','[class*="cmp" i]','[id*="cmp" i]','.fc-consent-root','#onetrust-consent-sdk','[class*="paywall" i]','[class*="modal" i]','[aria-modal="true"]','iframe','[id*="ad-" i]','[class*="adsby" i]','[class*="sticky" i][class*="ad" i]'];
    for (const s of kill) document.querySelectorAll(s).forEach(e => { if (e.tagName !== 'HTML' && e.tagName !== 'BODY') e.style.setProperty('display','none','important'); });
    document.documentElement.style.setProperty('overflow','auto','important'); document.body.style.setProperty('overflow','auto','important');
    document.querySelectorAll('*').forEach(e => { const cs = getComputedStyle(e); if ((cs.position === 'fixed' || cs.position === 'sticky') && e.getBoundingClientRect().height > 300) e.style.setProperty('display','none','important'); });
  });
  await new Promise(r => setTimeout(r, 500));
  await page.evaluate(() => window.scrollTo(0, 0)); await new Promise(r => setTimeout(r, 400));
  const marks = await page.evaluate((needles) => {
    const res = {};
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n; while ((n = walker.nextNode())) {
      for (const nd of needles) {
        if (res[nd]) continue;
        const i = n.textContent.indexOf(nd);
        if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + nd.length); const b = r.getBoundingClientRect(); if (b.width > 0) res[nd] = { x: b.x + scrollX, y: b.y + scrollY, w: b.width, h: b.height }; }
      }
    }
    return res;
  }, j.marks || []);
  const H = Math.min(j.maxH || 5000, await page.evaluate(() => document.documentElement.scrollHeight));
  await page.screenshot({ path: `gfx/assets/cap/${j.name}.png`, clip: { x: 0, y: 0, width: j.width || 1100, height: H }, captureBeyondViewport: true });
  out[j.name] = { url: j.url, width: j.width || 1100, height: H, dpr: 2, marks };
  console.log(j.name, H, Object.keys(marks).length + '/' + (j.marks || []).length);
  await page.close();
}
const prev = fs.existsSync('gfx/assets/cap/marks.json') ? JSON.parse(fs.readFileSync('gfx/assets/cap/marks.json','utf8')) : {};
fs.writeFileSync('gfx/assets/cap/marks.json', JSON.stringify(Object.assign(prev, out), null, 1));
await browser.close();
