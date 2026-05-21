#!/usr/bin/env node
// 把 mahjong/ 全部 inline 成單一 HTML,雙擊即可離線玩
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const indexHtml = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(ROOT, 'css', 'style.css'), 'utf8');

const jsFiles = ['tiles.js', 'win.js', 'tai.js', 'ai.js', 'game.js', 'render.js', 'main.js'];
const jsBundle = jsFiles.map(f => {
  const src = fs.readFileSync(path.join(ROOT, 'js', f), 'utf8');
  return `\n// === ${f} ===\n${src}`;
}).join('\n');

let html = indexHtml;
// 替換 CSS link
html = html.replace(
  /<link rel="stylesheet" href="css\/style\.css">/,
  `<style>\n${css}\n</style>`
);
// 替換所有 <script src="js/..."></script> 為單一 inline script
html = html.replace(
  /(\s*<script src="js\/[^"]+"><\/script>\s*)+/,
  `\n<script>\n${jsBundle}\n</script>\n`
);

const outPath = path.join(ROOT, 'mahjong-standalone.html');
fs.writeFileSync(outPath, html, 'utf8');
console.log(`Bundled → ${outPath}`);
console.log(`Size: ${(fs.statSync(outPath).size / 1024).toFixed(1)} KB`);
