// Renders the HR logo (school initials on a music staff) at every size the site and the APK need.
// Needs Playwright with Chromium: `node scripts/make_icons.js`.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const INK = '#131722', ORANGE = '#DD7428', WHITE = '#FFFFFF', EDGE = '#E3E6EE';
// Bricolage Grotesque ExtraBold H and R outlines (font units, baseline at 0), placed on a 100x100 grid.
const H = 'M435 0V-660H597V0ZM40 0V-660H202V0ZM161 -264V-400H520V-264Z';
const R = 'M40 0V-660H314Q358 -660 397.5 -652.5Q437 -645 469.5 -630.0Q502 -615 526.0 -592.0Q550 -569 563.0 -537.5Q576 -506 576 -466Q576 -435 565.5 -407.5Q555 -380 532.5 -358.0Q510 -336 474.5 -321.5Q439 -307 390 -301V-293Q454 -290 489.0 -268.0Q524 -246 541.5 -212.5Q559 -179 568 -140L603 0H424L399 -131Q393 -165 380.5 -186.0Q368 -207 345.0 -217.0Q322 -227 284 -227H202V0ZM202 -352H296Q351 -352 380.0 -373.0Q409 -394 409 -437Q409 -484 382.0 -507.0Q355 -530 300 -530H202Z';

function logo({ tile = 'rounded', scale = 1, line = 1.6 } = {}) {
  const bg = tile === 'rounded'
    ? `<rect x=".5" y=".5" width="99" height="99" rx="22" fill="${WHITE}" stroke="${EDGE}" stroke-width="1"/>`
    : tile === 'square' ? `<rect width="100" height="100" fill="${WHITE}"/>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">${bg}` +
    `<g transform="translate(50 50) scale(${scale}) translate(-50 -50)">` +
    `<path fill="none" stroke="${ORANGE}" stroke-width="${line}" d="M12 30H88M12 40H88M12 50H88M12 60H88M12 70H88"/>` +
    `<g fill="${INK}" stroke="${WHITE}" stroke-width="4.5" paint-order="stroke" stroke-linejoin="round">` +
    `<path transform="translate(18.25 66.5) scale(.05)" d="${H}"/><path transform="translate(49.6 66.5) scale(.05)" d="${R}"/></g></g></svg>`;
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
  fs.writeFileSync(path.join(ROOT, 'web', 'logo.svg'), logo());
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
