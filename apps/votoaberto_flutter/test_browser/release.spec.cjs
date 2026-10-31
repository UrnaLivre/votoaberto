const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const info = JSON.parse(fs.readFileSync('build/web/web-build.json'));
const folder = info.data_mode === 'real' ? 'real' : 'synthetic';
const dataRoot = `build/web/assets/assets/data/${folder}`;
const manifest = JSON.parse(fs.readFileSync(`${dataRoot}/manifest.json`));

async function semantics(page) {
  await page.locator('flt-glass-pane').waitFor({ state: 'attached' });
  await page.locator('flt-semantics-placeholder').evaluate(el => el.click());
  await expect(page.getByRole('link', { name: 'Uma iniciativa Urna Livre (abre em nova aba)' })).toBeVisible();
}

test('HTTP assets, MIME, security, cache and missing resources', async ({ request }) => {
  const checks = [
    ['/', 'text/html'], ['/flutter_bootstrap.js', /javascript/],
    ['/main.dart.js', /javascript/], ['/canvaskit/canvaskit.wasm', 'application/wasm'],
    ['/assets/assets/fonts/roboto-regular.ttf', /font|octet-stream/],
    ['/favicon.png', 'image/png'], [`/assets/assets/data/${folder}/manifest.json`, 'application/json'],
  ];
  for (const [url, mime] of checks) {
    const response = await request.get(url);
    expect(response.status(), url).toBe(200);
    expect(response.headers()['content-type'], url).toMatch(mime);
    expect(response.headers()['cache-control']).toBe('public, max-age=0, must-revalidate');
    expect(response.headers()['x-content-type-options']).toBe('nosniff');
    expect(response.headers()['x-frame-options']).toBe('DENY');
    expect(response.headers()['content-security-policy']).toBe("frame-ancestors 'none'");
  }
  for (const url of ['/missing.js', '/assets/missing.json', '/missing.png', '/missing.wasm', '/not-a-route', '/_headers']) {
    const response = await request.get(url);
    expect(response.status(), url).toBe(404);
    expect(await response.text(), url).not.toContain('<base href="/">');
  }
  for (const name of ['manifest.json', ...Object.keys(manifest.artifacts)]) {
    const response = await request.get(`/assets/assets/data/${folder}/${name}`);
    expect(response.ok(), name).toBeTruthy();
    expect(Buffer.compare(await response.body(), fs.readFileSync(path.join(dataRoot, name))), name).toBe(0);
  }
});

for (const [name, viewport] of [
  ['desktop', { width: 1366, height: 900 }],
  ['mobile', { width: 390, height: 844 }],
  ['landscape', { width: 844, height: 390 }],
  ['small-window', { width: 800, height: 600 }],
]) {
  test(`${name}: startup, data, deep link, history and institutional link`, async ({ page, context }) => {
    await page.setViewportSize(viewport);
    const errors = [];
    const failed = [];
    const external = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400) failed.push(response.url()); });
    page.on('request', request => {
      if (/^https?:/.test(request.url()) && !request.url().startsWith('http://127.0.0.1:8787/')) external.push(request.url());
    });
    await page.goto('/#/uf/SC?modo=2');
    await semantics(page);
    await expect(page.getByText('Santa Catarina', { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/Não foi possível carregar os dados/)).toHaveCount(0);
    await page.reload();
    await semantics(page);
    await expect(page.getByText('Santa Catarina', { exact: true }).first()).toBeVisible();
    await page.evaluate(() => { location.hash = '/mundo?modo=1'; });
    await expect(page.getByText('Consultar votação no Brasil', { exact: true })).toBeVisible();
    await page.goBack();
    await expect(page.getByText('Santa Catarina', { exact: true }).first()).toBeVisible();
    await page.goForward();
    await expect(page.getByText('Consultar votação no Brasil', { exact: true })).toBeVisible();
    const link = page.getByRole('link', { name: 'Uma iniciativa Urna Livre (abre em nova aba)' });
    await link.scrollIntoViewIfNeeded();
    await link.focus();
    const popupPromise = context.waitForEvent('page');
    await link.press('Enter');
    const popup = await popupPromise;
    await popup.waitForURL('https://urnalivre.com.br/**');
    expect(await popup.evaluate(() => window.opener === null)).toBeTruthy();
    await popup.close();
    await expect(page).toHaveURL(/127\.0\.0\.1:8787\/.*#\/mundo/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    await page.screenshot({ path: `test-results/${name}.png` });
    expect(errors).toEqual([]);
    expect(failed).toEqual([]);
    expect(external).toEqual([]);
  });
}

test('legacy Flutter worker retires without removing unrelated caches', async ({ page }) => {
  await page.goto('/');
  await semantics(page);
  await page.evaluate(async () => {
    await navigator.serviceWorker.register('/flutter_service_worker.js');
    await navigator.serviceWorker.ready;
    await caches.open('flutter-app-cache');
    await caches.open('unrelated-test-cache');
  });
  await page.reload();
  await semantics(page);
  const state = await page.evaluate(async () => ({
    registrations: (await navigator.serviceWorker.getRegistrations()).length,
    caches: await caches.keys(),
    controlled: navigator.serviceWorker.controller !== null,
  }));
  expect(state.registrations).toBe(0);
  expect(state.controlled).toBeFalsy();
  expect(state.caches).not.toContain('flutter-app-cache');
  expect(state.caches).toContain('unrelated-test-cache');
});

test('dark theme and 2x visual viewport zoom keep the footer reachable', async ({ page, context }) => {
  await page.setViewportSize({ width: 800, height: 600 });
  await page.goto('/#/uf/SC?modo=1');
  await semantics(page);
  await page.getByRole('button', { name: 'Usar tema escuro' }).click();
  await expect(page.getByRole('button', { name: 'Usar tema claro' })).toBeVisible();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
  expect(await page.evaluate(() => visualViewport.scale)).toBe(2);
  await page.getByRole('link', { name: 'Uma iniciativa Urna Livre (abre em nova aba)' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'test-results/dark-visual-zoom-2x.png' });
});

test('real overseas special cases preserve missing second round and results', async ({ page }) => {
  test.skip(info.data_mode !== 'real', 'Special cases belong to the existing real dataset only.');
  await page.goto('/#/mundo?modo=1');
  await semantics(page);
  await page.getByRole('button', { name: /Casos especiais \(2\)/ }).click();
  await expect(page.getByText('Localidade eleitoral TSE 29432', { exact: true })).toBeVisible();
  await page.getByRole('tab', { name: /Trípoli/ }).click();
  await expect(page.getByText('Localidade eleitoral TSE 30686', { exact: true })).toBeVisible();
  const missing = page.getByText('Não há registro de resultados desta localidade para o 2º turno na base consultada.');
  await missing.scrollIntoViewIfNeeded();
  await expect(missing).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: /Casos especiais \(2\)/ })).toBeVisible();
});
