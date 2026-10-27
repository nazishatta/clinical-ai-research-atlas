const { chromium } = require('playwright');
const OUT=process.env.OUT_DIR||'.';
const URL=process.argv[2]||'http://localhost:8501';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1400,height:1000}});
  const idle = async () => { await p.waitForTimeout(800); await p.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, {timeout:60000}).catch(()=>{}); await p.waitForTimeout(1200); };
  const metric = async () => (await p.locator('[data-testid="stMetricValue"]').first().innerText());
  const topicVal = async () => (await p.locator('[data-testid="stSidebar"] input[aria-label="NMF topic"]').inputValue());
  await p.goto(URL); await p.waitForSelector('[data-testid="stMetricValue"]',{timeout:90000}); await idle();
  console.log('start', await metric(), '|', (await topicVal()).replace(/\n/g,' '));
  // choose topic option 2
  await p.locator('[data-testid="stSidebar"] [data-testid="stSelectbox"]').first().click();
  await p.locator('[role="option"]').nth(1).click(); await idle();
  console.log('topic set', await metric(), '|', (await topicVal()).replace(/\n/g,' '));
  await p.getByRole('button',{name:'Reset all filters'}).click(); await idle();
  console.log('after reset', await metric(), '|', (await topicVal()).replace(/\n/g,' '));
  // nudge the year slider start with keyboard
  const thumb = p.locator('[data-testid="stSidebar"] input[aria-label="Publication years — start"]'); await thumb.focus(); await p.keyboard.press('ArrowRight'); await idle();
  console.log('after year change', await metric(), '|', (await topicVal()).replace(/\n/g,' '));
  await p.screenshot({path:require('path').join(OUT,'after_reset.png')});
  await b.close();
})();
