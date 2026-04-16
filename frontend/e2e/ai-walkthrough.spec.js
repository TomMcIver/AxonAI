const { test, expect } = require('@playwright/test');

const ACTION_WAIT_MS = 10000;
const STEP_SCROLL_MS = 1200;

async function waitAction(page) {
  await page.waitForTimeout(ACTION_WAIT_MS);
}

async function clickByText(page, text, options = {}) {
  const { exact = false, timeout = 15000 } = options;
  const locator = page.getByRole('button', { name: text, exact }).first();
  await locator.waitFor({ state: 'visible', timeout });
  await locator.click({ timeout });
}

/** Navigate like the sidebar menu would — uses routes only (no hamburger / overlay). */
async function openRoute(page, route) {
  await page.goto(route, { waitUntil: 'domcontentloaded' });
  await waitAction(page);
}

async function smoothScrollToBottom(page) {
  const viewportHeight = page.viewportSize()?.height || 900;
  const step = Math.max(180, Math.floor(viewportHeight * 0.22));
  const maxSteps = 200;
  let lastY = -1;
  let stagnant = 0;

  for (let i = 0; i < maxSteps; i += 1) {
    const y = await page.evaluate(() => window.scrollY);
    const maxScroll = await page.evaluate(
      () => Math.max(0, document.documentElement.scrollHeight - window.innerHeight),
    );
    if (y >= maxScroll - 2) break;
    if (Math.abs(y - lastY) < 2) {
      stagnant += 1;
      if (stagnant >= 4) break;
    } else {
      stagnant = 0;
    }
    lastY = y;
    await page.mouse.wheel(0, step);
    await page.waitForTimeout(STEP_SCROLL_MS);
  }

  await page.waitForTimeout(2000);
}

async function gentleGraphDrag(page) {
  const graphTarget = page.locator('canvas, svg').first();
  if ((await graphTarget.count()) === 0) return;
  const box = await graphTarget.boundingBox();
  if (!box) return;

  const startX = box.x + box.width * 0.55;
  const startY = box.y + box.height * 0.55;

  await page.mouse.move(startX, startY, { steps: 30 });
  await page.waitForTimeout(700);
  await page.mouse.down();
  await page.mouse.move(startX + 120, startY + 50, { steps: 90 });
  await page.waitForTimeout(300);
  await page.mouse.move(startX - 80, startY + 20, { steps: 80 });
  await page.mouse.up();
  await page.waitForTimeout(1500);
}

test('AI-style full website walkthrough with single video', async ({ page }) => {
  test.setTimeout(20 * 60 * 1000);

  // Login -> Teacher (same as clicking the role; we only use click on login cards).
  await openRoute(page, '/login');
  await expect(page).toHaveURL(/\/login/);
  await clickByText(page, 'Teacher');
  await waitAction(page);
  await expect(page).toHaveURL(/\/teacher/);

  // Teacher dashboard: scroll slowly and interact with graph gently.
  await smoothScrollToBottom(page);
  await gentleGraphDrag(page);
  await smoothScrollToBottom(page);

  // Same order as the sidebar menu, but via routes (no menu UI clicks).
  await openRoute(page, '/teacher/students');
  await smoothScrollToBottom(page);

  await openRoute(page, '/teacher/subjects');
  await smoothScrollToBottom(page);

  await openRoute(page, '/teacher/knowledge-graph');
  await smoothScrollToBottom(page);
  await gentleGraphDrag(page);

  await openRoute(page, '/teacher/settings');
  await smoothScrollToBottom(page);

  await openRoute(page, '/teacher');
  await smoothScrollToBottom(page);

  // Student
  await openRoute(page, '/login');
  await clickByText(page, 'Student');
  await waitAction(page);
  await expect(page).toHaveURL(/\/student/);
  await smoothScrollToBottom(page);

  // Parent
  await openRoute(page, '/login');
  await clickByText(page, 'Parent / Whanau');
  await waitAction(page);
  await expect(page).toHaveURL(/\/parent/);
  await smoothScrollToBottom(page);

  // End on login screen.
  await openRoute(page, '/login');
  await expect(page.getByText(/Choose how you're signing in|Choose how you/)).toBeVisible();
  await waitAction(page);
});
