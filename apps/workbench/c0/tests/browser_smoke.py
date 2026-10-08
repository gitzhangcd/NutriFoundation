from pathlib import Path
from playwright.sync_api import sync_playwright
base=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda err: errors.append(str(err)))
    page.set_content((base/'prototype/index.html').read_text(), wait_until='load')
    assert page.get_by_text('专家任务中心').count()==1
    page.get_by_text('Pre-AI 独立判断',exact=False).first.click()
    assert page.get_by_text('专家分阶段判断').count()==1
    assert page.locator('body').inner_text().find('合成 Agent 候选')<0
    page.get_by_text('测试未授权访问').click()
    assert page.get_by_text('拒绝：当前协议阶段无权访问 Agent 内容',exact=False).count()==1
    page.get_by_text('下一阶段 →').first.click()
    assert page.get_by_text('缺失信息',exact=False).count()>0
    page.screenshot(path=str(base/'prototype/screenshot-r2-pre.png'),full_page=True)
    page.get_by_text('我的任务').first.click()
    page.get_by_text('Agent-first 验证（待候选冻结）').first.click()
    assert page.get_by_text('R1 入口保持锁定').count()==1
    page.get_by_text('我的任务').first.click()
    page.get_by_text('Agent-first 候选核查').first.click()
    page.get_by_text('查看合成候选与来源').click()
    assert page.get_by_text('合成 Agent 候选',exact=True).count()==1
    assert page.locator('select option').count()==6
    page.screenshot(path=str(base/'prototype/screenshot-r1-verify.png'),full_page=True)
    assert not errors,errors
    browser.close()
    print('C0 BROWSER SMOKE PASS: R2 preAI deny, staged interaction, R1 hold, R1 synthetic verify, 6 dispositions; JS errors=0')