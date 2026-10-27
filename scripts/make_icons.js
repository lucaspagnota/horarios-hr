// Renders the HR logo (school initials on a music staff) at every size the site and the APK need.
// Needs Playwright's Chromium once: `npx playwright install chromium`, then `npm run icons`.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
// The logo lives in app/horarios-hr.html (the LOGO constant and the --brand-* colors); this reads it from there
// so the icons always match what the app shows.
const APP = fs.readFileSync(path.join(ROOT, 'app', 'horarios-hr.html'), 'utf8');
const pick = (re, what, src = APP) => { const m = src.match(re); if (!m) throw new Error(`Não achei ${what} em app/horarios-hr.html`); return m[1]; };
const INK = pick(/--brand-ink:(#[0-9A-Fa-f]{6})/, '--brand-ink');
const ORANGE = pick(/--brand-orange:(#[0-9A-Fa-f]{6})/, '--brand-orange');
const WHITE = pick(/--brand-paper:(#[0-9A-Fa-f]{6})/, '--brand-paper');
const EDGE = '#E3E6EE';
const LOGO = pick(/const LOGO = `([^`]+)`/, 'a constante LOGO');
const STAFF = pick(/class="st"[^>]*\bd="([^"]+)"/, 'a pauta do LOGO', LOGO);
const LETTERS = pick(/<g class="lt"[^>]*>(.*?)<\/g>/, 'as letras do LOGO', LOGO);

function logo({ tile = 'rounded', scale = 1, line = 1.6 } = {}) {
  const bg = tile === 'rounded'
    ? `<rect x=".5" y=".5" width="99" height="99" rx="22" fill="${WHITE}" stroke="${EDGE}" stroke-width="1"/>`
    : tile === 'square' ? `<rect width="100" height="100" fill="${WHITE}"/>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">${bg}` +
    `<g transform="translate(50 50) scale(${scale}) translate(-50 -50)">` +
    `<path fill="none" stroke="${ORANGE}" stroke-width="${line}" d="${STAFF}"/>` +
    `<g fill="${INK}" stroke="${WHITE}" stroke-width="4.5" paint-order="stroke" stroke-linejoin="round">` +
    `${LETTERS}</g></g></svg>`;
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  async function png(file, size, svg, canvas = null) {
    // canvas: { size, color } draws the logo at `size` centred on a bigger plain background (splash screens).
    const box = canvas ? canvas.size : size;
    await page.setViewportSize({ width: box, height: box });
    await page.setContent(`<html><body style="margin:0;background:${canvas ? canvas.color : 'transparent'};display:grid;place-items:center;width:${box}px;height:${box}px">
      <div style="width:${size}px;height:${size}px">${svg.replace('<svg ', `<svg width="${size}" height="${size}" `)}</div></body></html>`);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    await page.screenshot({ path: file, omitBackground: !canvas });
  }
  const web = path.join(ROOT, 'web', 'icons');
  await png(path.join(web, 'icon-192.png'), 192, logo());
  await png(path.join(web, 'icon-512.png'), 512, logo());
  await png(path.join(web, 'icon-maskable-512.png'), 512, logo({ tile: 'square', scale: 0.8 }));
  await png(path.join(web, 'apple-touch-icon.png'), 180, logo({ tile: 'square', scale: 0.9 }));
  await png(path.join(web, 'favicon.png'), 64, logo({ line: 3 }));
  const assets = path.join(ROOT, 'assets');
  await png(path.join(assets, 'icon-only.png'), 1024, logo({ tile: 'square', scale: 0.86 }));
  await png(path.join(assets, 'icon-foreground.png'), 1024, logo({ tile: 'none', scale: 0.62 }));
  await png(path.join(assets, 'icon-background.png'), 1024, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="${WHITE}"/></svg>`);
  await png(path.join(assets, 'splash.png'), 420, logo(), { size: 2732, color: '#F4F5F9' });
  await png(path.join(assets, 'splash-dark.png'), 420, logo(), { size: 2732, color: '#0E1017' });
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
