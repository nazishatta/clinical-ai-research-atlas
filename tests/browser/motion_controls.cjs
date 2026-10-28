// Real-browser check of the animation controls (Pause/Resume, Replay, Show final values),
// with normal motion and with the system "reduced motion" preference.
// Usage: node tests/browser/motion_controls.cjs [http://localhost:8501]
// Exits 1 if any expectation fails. Requires: npm install playwright
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8501';
const failures = [];
function expect(label, ok, detail) {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${detail ? ' — ' + detail : ''}`);
  if (!ok) failures.push(label);
}
async function chartFrame(page) {
  await page.goto(URL);
  await page.waitForSelector('[data-testid="stMetricValue"]', { timeout: 90000 });
  await page.getByRole('tab', { name: 'Research Evolution' }).click();
  const handle = await page.waitForSelector('iframe[title^="Works per year"]', { timeout: 60000 });
  await handle.scrollIntoViewIfNeeded();
  const frame = await handle.contentFrame();
  await frame.waitForSelector('button.atlas-btn', { timeout: 60000 });
  return frame;
}
const statusText = (frame) => frame.locator('[role="status"]').innerText();
(async () => {
  const browser = await chromium.launch();
  try {
    // Normal motion.
    const page = await (await browser.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
    const frame = await chartFrame(page);
    for (const name of ['Pause', 'Replay', 'Show final values']) {
      expect(`button "${name}" exists and is a real button`, await frame.getByRole('button', { name }).count() === 1);
    }
    expect('controls are a labelled group', await frame.locator('[role="group"][aria-label="Chart animation controls"]').count() === 1);
    await frame.getByRole('button', { name: 'Replay' }).click();
    await page.waitForTimeout(300);
    expect('Replay starts playback', (await statusText(frame)) === 'Playing', await statusText(frame));
    await frame.getByRole('button', { name: 'Pause' }).click();
    expect('Pause pauses', (await statusText(frame)) === 'Paused', await statusText(frame));
    expect('Pause button turns into Resume (aria-pressed=true)',
      (await frame.getByRole('button', { name: 'Resume' }).getAttribute('aria-pressed')) === 'true');
    await frame.getByRole('button', { name: 'Resume' }).click();
    expect('Resume continues', (await statusText(frame)) === 'Playing', await statusText(frame));
    await frame.getByRole('button', { name: 'Show final values' }).click();
    expect('Show final values completes', (await statusText(frame)) === 'Showing final values', await statusText(frame));
    const clipped = await frame.$$eval('.barlayer, .scatterlayer', els => els.some(e => e.style.clipPath && e.style.clipPath !== 'none'));
    expect('all marks visible after Show final values', !clipped);
    // Keyboard: Tab reaches the first control.
    await frame.locator('body').click({ position: { x: 5, y: 5 } });
    await page.keyboard.press('Tab');
    const focused = await frame.evaluate(() => document.activeElement && document.activeElement.textContent);
    expect('Tab moves keyboard focus onto a control', ['Pause', 'Resume', 'Replay', 'Show final values'].includes(focused), focused);

    // Reduced motion.
    const reducedPage = await (await browser.newContext({ viewport: { width: 1400, height: 1000 }, reducedMotion: 'reduce' })).newPage();
    const rframe = await chartFrame(reducedPage);
    await reducedPage.waitForTimeout(500);
    expect('reduced motion: final values shown at once', (await statusText(rframe)).startsWith('Showing final values'), await statusText(rframe));
    expect('reduced motion: Pause and Replay disabled',
      (await rframe.getByRole('button', { name: 'Pause' }).isDisabled()) && (await rframe.getByRole('button', { name: 'Replay' }).isDisabled()));
  } catch (err) {
    console.log('FAIL  script error: ' + err.message);
    failures.push('script error');
  } finally {
    await browser.close();
  }
  console.log(failures.length ? `\n${failures.length} check(s) failed.` : '\nAll motion-control checks passed.');
  process.exit(failures.length ? 1 : 0);
})();
