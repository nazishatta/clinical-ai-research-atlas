// Real-browser regression check for "Reset all filters".
// Usage: node tests/browser/reset_browser.cjs [http://localhost:8501]
// Exits 1 if any expectation fails. Requires: npm install playwright
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8501';
const failures = [];
function expect(label, actual, expected) {
  const ok = actual === expected;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}: got ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
  if (!ok) failures.push(label);
}
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const idle = async () => {
    await page.waitForTimeout(800);
    await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1500);
  };
  const works = async () => (await page.locator('[data-testid="stMetricValue"]').first().innerText()).trim();
  const topic = () => page.locator('[data-testid="stSidebar"] input[aria-label="NMF topic"]').inputValue();
  try {
    await page.goto(URL);
    await page.waitForSelector('[data-testid="stMetricValue"]', { timeout: 90000 });
    await idle();
    expect('start: selected works', await works(), '1,395');
    expect('start: topic box', await topic(), 'All topics');

    await page.locator('[data-testid="stSidebar"] input[aria-label="NMF topic"]').click();
    await page.locator('[role="option"]').nth(1).click();
    await idle();
    expect('after choosing T1: selected works', await works(), '200');

    await page.getByRole('button', { name: 'Reset all filters' }).click();
    await idle();
    expect('after reset: selected works', await works(), '1,395');
    expect('after reset: topic box', await topic(), 'All topics');

    const start = page.locator('[data-testid="stSidebar"] input[aria-label="Publication years — start"]');
    await start.focus();
    await page.keyboard.press('ArrowRight');
    await idle();
    expect('after moving start year to 2017: selected works', await works(), '1,390');
    expect('after moving start year to 2017: topic box', await topic(), 'All topics');
  } catch (err) {
    console.log('FAIL  script error: ' + err.message);
    failures.push('script error');
  } finally {
    await browser.close();
  }
  console.log(failures.length ? `\n${failures.length} check(s) failed.` : '\nAll reset checks passed.');
  process.exit(failures.length ? 1 : 0);
})();
