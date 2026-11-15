const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');

// Exercise the production runtime with a minimal DOM, without publishing test hooks.
const source = fs.readFileSync('frontend/app.js', 'utf8');
const instrumented = source.slice(0, source.indexOf('  const initialJob =')) + `
  globalThis.runtime = {submitLive, requestJSON, wakeService, beginLive, cancelLive,
    snapshot:()=>({activeJobId,liveResult,liveError,liveBusy,current}),
    startTour, stopTour, runTourStep, pauseTour};
})();`;
function harness(fetch) {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      id, innerHTML:'', textContent:'', value:'', disabled:false, hidden:false,
      classList:{add(){},remove(){},toggle(){}},
      addEventListener(){},removeEventListener(){},focus(){},setAttribute(){},removeAttribute(){},
      querySelectorAll(){return [];},querySelector(){return element('queried');},
      prepend(){},getBoundingClientRect(){return {left:0,top:0,width:100,height:40};},
      animate(){return {cancel(){},pause(){},play(){},playState:'finished'};},
      closest(){return null;}
    });
    return elements.get(id);
  };
  const main=element('main');
  const document={getElementById:element,querySelector:()=>element('queried'),querySelectorAll:()=>[],
    addEventListener(){},body:{dataset:{page:'entry'},classList:{add(){},remove(){},toggle(){}}},
    activeElement:element('main'),hidden:false};
  const window={addEventListener(){},scrollTo(){},print(){}};
  const context=vm.createContext({document,window,fetch,URL,URLSearchParams,FormData,AbortController,DOMException,
    Date,performance,console,setTimeout,clearTimeout,setInterval,clearInterval,innerWidth:1200,innerHeight:900,scrollY:0,
    location:{hostname:'localhost',href:'http://localhost:8767/index.html',search:''},
    history:{replaceState(){}},navigator:{},matchMedia:()=>({matches:true})});
  vm.runInContext(instrumented,context);
  return {runtime:context.runtime,main};
}
const json=body=>({ok:true,status:200,headers:{get:()=> 'application/json'},json:async()=>body});
const form=()=>{const data=new FormData();data.append('case_text','A synthetic clinical case with sufficient detail.');return data;};

test('both services respond before exactly one upload; real result replaces fixtures',async()=>{
  const calls=[];
  const result={patient_summary:'Actual response summary',possible_conditions:[],red_flags:[],suggested_next_steps:[],missing_information:[],urgency:'Non-urgent',clinical_note:'Returned note'};
  const {runtime,main}=harness(async(url,options)=>{
    calls.push({url,method:options.method||'GET'});
    if(url==='http://127.0.0.1:8000/health')return json({status:'ok'});
    if(url==='http://127.0.0.1:8001/health')return json({http_service:'awake'});
    if(url.endsWith('/jobs/upload'))return json({job_id:'test-001'});
    return json({status:'done',result});
  });
  await runtime.submitLive(form());
  assert.equal(calls.filter(c=>c.method==='POST').length,1);
  assert.deepEqual(calls.slice(0,2).map(c=>c.url).sort(),['http://127.0.0.1:8000/health','http://127.0.0.1:8001/health']);
  assert.equal(runtime.snapshot().current,'results');
  assert.match(main.innerHTML,/Actual response summary/);
  assert.match(main.innerHTML,/non-urgent/);
  assert.doesNotMatch(main.innerHTML,/Pneumonia/);
  runtime.cancelLive();
});

test('ambiguous upload is never automatically retried',async()=>{
  let posts=0;
  const {runtime}=harness(async(url,options)=>{
    if(options.method==='POST'){posts++;throw new TypeError('Connection lost');}
    return json(url.includes(':8001')?{http_service:'awake'}:{status:'ok'});
  });
  await runtime.submitLive(form());
  assert.equal(posts,1);assert.equal(runtime.snapshot().liveError.kind,'uncertain');
  assert.equal(runtime.snapshot().liveBusy,false);runtime.cancelLive();
});

test('concurrent submit requests are deduplicated',async()=>{
  let posts=0;
  const {runtime}=harness(async(url,options)=>{
    if(options.method==='POST'){posts++;return json({job_id:'test-002'});}
    if(url.includes('/jobs/result'))return json({status:'failed'});
    return json(url.includes(':8001')?{http_service:'awake'}:{status:'ok'});
  });
  await Promise.all([runtime.submitLive(form()),runtime.submitLive(form())]);
  assert.equal(posts,1);assert.equal(runtime.snapshot().liveError.kind,'failed');runtime.cancelLive();
});

test('loading HTML and opaque health responses cannot establish readiness',async()=>{
  const {runtime}=harness(async()=>({ok:true,headers:{get:()=> 'text/html'},json:async()=>({status:'ok'})}));
  await assert.rejects(runtime.requestJSON('/health',{},new AbortController().signal,100));
  const run=runtime.beginLive();
  await assert.rejects(runtime.wakeService('/health',body=>body.status==='ok','status',Date.now()+5,run),/Startup timed out/);
  runtime.cancelLive();
});

test('canceled request does not reach the network',async()=>{
  let requests=0;const {runtime}=harness(async()=>{requests++;return json({});});
  const controller=new AbortController();controller.abort();
  await assert.rejects(runtime.requestJSON('/health',{},controller.signal,100));assert.equal(requests,0);
});

test('browser-blocked startup stops with recovery guidance and never uploads',async()=>{
  let posts=0;
  const {runtime}=harness(async(url,options)=>{
    if(options.method==='POST')posts++;
    throw new TypeError('Failed to fetch');
  });
  await runtime.submitLive(form());
  assert.equal(posts,0);
  assert.equal(runtime.snapshot().liveBusy,false);
  assert.match(runtime.snapshot().liveError.message,/ERR_BLOCKED_BY_CLIENT/);
  runtime.cancelLive();
});

test('demo playback is isolated from live network calls',()=>{
  let requests=0;const {runtime}=harness(async()=>{requests++;return json({});});
  runtime.startTour();runtime.runTourStep(1);runtime.runTourStep(2);runtime.runTourStep(3);runtime.runTourStep(4);runtime.stopTour();
  assert.equal(requests,0);assert.equal(runtime.snapshot().activeJobId,null);
});

test('model strings are escaped and truthy verification strings are not trusted',async()=>{
  const result={patient_summary:'<script>alert(1)</script>',possible_conditions:[{condition:'<img src=x onerror=alert(1)>',icd10:'javascript:alert(1)',likelihood:'High',reasoning:'<b>reason</b>',icd10_verified:'true'}],red_flags:['<svg onload=alert(1)>'],suggested_next_steps:[],missing_information:[],urgency:'invented',clinical_note:'<i>note</i>'};
  const {runtime,main}=harness(async(url,options)=>{
    if(options.method==='POST')return json({job_id:'test-003'});
    if(url.includes('/jobs/result'))return json({status:'done',result});
    return json(url.includes(':8001')?{http_service:'awake'}:{status:'ok'});
  });
  await runtime.submitLive(form());
  assert.match(main.innerHTML,/&lt;script&gt;/);assert.match(main.innerHTML,/Code not verified/);
  assert.doesNotMatch(main.innerHTML,/<script>|<img src=x|href="javascript:/);
  assert.match(main.innerHTML,/urgency-banner unavailable/);runtime.cancelLive();
});

test('opaque responses are rejected',async()=>{
  const {runtime}=harness(async()=>({ok:false,status:0,type:'opaque'}));
  await assert.rejects(runtime.requestJSON('/health',{},new AbortController().signal,100));
});
