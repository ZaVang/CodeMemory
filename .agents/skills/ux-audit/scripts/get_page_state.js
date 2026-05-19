// scripts/get_page_state.js
const puppeteer = require('puppeteer');

(async () => {
  const targetUrl = process.argv[2] || 'http://localhost:3000';

  try {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    
    // 等待网络空闲，确保 SPA 框架渲染完成
    await page.goto(targetUrl, { waitUntil: 'networkidle0', timeout: 15000 });

    // 提取页面的语义化结构和交互节点
    const pageState = await page.evaluate(() => {
      // 1. 提取核心文本内容（剥离复杂的 DOM 结构）
      const cleanText = document.body.innerText.replace(/\n{3,}/g, '\n\n');

      // 2. 提取所有可交互元素（模拟读屏软件的焦点表）
      const interactiveSelectors = 'button, a, input, select, textarea, [role="button"]';
      const elements = Array.from(document.querySelectorAll(interactiveSelectors));
      
      const actionNodes = elements.map((el, index) => {
        const tag = el.tagName.toLowerCase();
        const text = el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || '无文本标签';
        const isHidden = window.getComputedStyle(el).display === 'none';
        const isDisabled = el.disabled;
        
        return `[ID: ${index}] <${tag}> "${text.trim().substring(0, 30)}" ${isHidden ? '(不可见)' : ''} ${isDisabled ? '(已禁用)' : ''}`;
      }).filter(node => !node.includes('(不可见)'));

      return {
        title: document.title,
        url: window.location.href,
        content_snapshot: cleanText.substring(0, 2000), // 防止超长截断
        interactive_elements: actionNodes
      };
    });

    console.log(JSON.stringify(pageState, null, 2));
    await browser.close();

  } catch (error) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
})();