// TeX -> standalone SVG (no font cache, glyphs inlined), one per line of a JSON array on argv[2]
const { mathjax } = require('mathjax-full/js/mathjax.js');
const { TeX } = require('mathjax-full/js/input/tex.js');
const { AllPackages } = require('mathjax-full/js/input/tex/AllPackages.js');
const { SVG } = require('mathjax-full/js/output/svg.js');
const { liteAdaptor } = require('mathjax-full/js/adaptors/liteAdaptor.js');
const { RegisterHTMLHandler } = require('mathjax-full/js/handlers/html.js');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const doc = mathjax.document('', { InputJax: new TeX({ packages: AllPackages }), OutputJax: new SVG({ fontCache: 'none' }) });
const out = JSON.parse(process.argv[2]).map(function (t) {
  return adaptor.innerHTML(doc.convert(t, { display: true }));
});
process.stdout.write(JSON.stringify(out));
