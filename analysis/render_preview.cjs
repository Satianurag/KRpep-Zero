// Headless QA of our local static dashboard; no user browser/profile access.
const fs = require('node:fs');
const path = require('node:path');
 const { chromium } = require(process.env.KRPEP_PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1600,height:1200},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:8873/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>window.STRUCTURE_READY||window.STRUCTURE_ERROR,{timeout:60000});
 const state=await page.evaluate(()=>({ready:window.STRUCTURE_READY,error:window.STRUCTURE_ERROR}));
 if(!state.ready)throw Error(JSON.stringify(state));
 await page.screenshot({path:'results/figures/dashboard-preview.png',fullPage:false});
 await page.locator('#pocket').click();
 await page.locator('#surface').click();
 await page.locator('#surface').click();
 await page.locator('#whole').click();
 if(errors.length)throw Error(errors.join('\n'));
 const controlRows=await page.locator('#campaign tbody tr').count();
 if(controlRows!==6)throw Error('Expected all six control rows');
 if(!await page.locator('#campaign').innerText().then(t=>/predeclared qc gate failed/i.test(t)))throw Error('Missing stop decision');
 await page.locator('#campaign').screenshot({path:'results/figures/dashboard-controls.png'});
 let remediationRows=0;
 if(await page.locator('#remediation tbody').count()){
  remediationRows=await page.locator('#remediation tbody tr').count();
  if(remediationRows!==6)throw Error('Expected all six revision-2 rows');
  await page.locator('#remediation').screenshot({path:'results/figures/dashboard-remediation.png'});
 }
 const runRows=await page.locator('#runs tbody tr').count();
 if(runRows!==18)throw Error('Expected all 18 saved control predictions');
 const runs=await page.locator('.run-button').evaluateAll(es=>es.map(e=>e.dataset.runId));
 for(const id of runs){
  await page.locator(`.run-button[data-run-id="${id}"]`).click();
  await page.locator(`#molecule[data-loaded-run="${id}"][aria-busy="false"]`).waitFor();
  if(!await page.locator('#load-status').innerText().then(t=>t.includes('Recorded coordinates loaded')))throw Error('Failed view '+id);
  if(id.includes('scramble')){
   if(await page.locator('#pose-value').innerText()!=='—'||await page.locator('#contacts-value').innerText()!=='—')throw Error('Scramble pose metric must be NA');
  }
 }
 await page.locator('#protocol-select').selectOption('reference');
 await page.locator('#molecule[data-loaded-run="reference"][aria-busy="false"]').waitFor();
 const brokenLinks=[];
 for(const link of await page.locator('a[href]').evaluateAll(es=>es.map(e=>e.getAttribute('href')))){
  if(link.startsWith('#')||/^https?:/.test(link))continue;
  const response=await page.request.get('http://127.0.0.1:8873/'+link);
  if(!response.ok())brokenLinks.push(link);
 }
 if(brokenLinks.length)throw Error('Broken report links: '+brokenLinks.join(', '));
 await page.setViewportSize({width:390,height:844});
 await page.reload({waitUntil:'networkidle'});await page.waitForFunction(()=>window.STRUCTURE_READY);
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
 const clippedTables=await page.locator('table').evaluateAll(ts=>ts.filter(t=>t.getBoundingClientRect().width>t.parentElement.clientWidth+1&&getComputedStyle(t.parentElement).overflowX==='hidden').map(t=>t.innerText.slice(0,60)));
 await page.screenshot({path:'results/figures/dashboard-mobile.png',fullPage:false});
 fs.writeFileSync('results/figures/dashboard-qa.json',JSON.stringify({ready:state.ready,pageErrors:errors,mobileHorizontalOverflow:overflow,clippedTables,renderer:'3Dmol.js2.5.5',controlRows,remediationRows,runRows,predictionViewsChecked:runs.length,brokenLinks,scope:'Local dashboard QA only; no new standalone molecular render'},null,2));
 await browser.close();
 if(overflow)throw Error('Mobile horizontal overflow');
 if(clippedTables.length)throw Error('Clipped mobile table: '+clippedTables.join(', '));
 console.log('Dashboard and molecular-render QA passed');
})().catch(e=>{console.error(e);process.exit(1)});
