'use strict';
(() => {
  const main = document.getElementById('main');
  const stateSelect = document.getElementById('preview-state');
  const announcement = document.getElementById('announcement');
  const sample = `62-year-old man presenting with four days of fever and productive cough, followed by worsening shortness of breath over the past 24 hours. He initially became breathless climbing stairs and now feels breathless while sitting. Sputum is yellow, without blood. He reports right-sided discomfort with deep inspiration, reduced appetite and fatigue. He denies recent surgery, prolonged travel, unilateral leg swelling, syncope or known sick contacts.

History includes hypertension and type 2 diabetes. He has no known asthma, chronic lung disease, previous venous thromboembolism or heart failure. He stopped smoking 12 years ago after approximately 15 pack-years. Regular medications are metformin 500 mg twice daily and amlodipine 5 mg daily. He reports a penicillin-associated rash in childhood, without documented anaphylaxis.

At assessment: temperature 38.4°C, heart rate 108/min, blood pressure 132/78 mmHg, respiratory rate 26/min and oxygen saturation 91% on room air. He is alert, answers questions appropriately and speaks in short sentences. Examination documents right basal crackles, no wheeze, no peripheral edema and no calf asymmetry. Oral intake has decreased, but he reports passing urine. Chest imaging, blood count, renal function, respiratory pathogen testing and a previous baseline oxygen saturation are not yet available.`;
  const sampleSummary = '62-year-old man with fever, productive cough and progressive breathlessness, now at rest. Temperature 38.4°C, pulse 108/min, respiratory rate 26/min and oxygen saturation 91% on room air; right basal crackles. Background hypertension and type 2 diabetes. Imaging and laboratory results are pending.';
  const jobId = 'demo-case-001';
  let draft = '', chosenFile = null, current = 'results', mode = 'text', autoDemo = false;
  let timers = [], seconds = 0, walkthrough = false, tour = null;
  const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const examples = [
    {label:'Respiratory symptoms', text:sample},
    {label:'Chest discomfort', text:`48-year-old woman presenting with two days of intermittent central chest pressure. Episodes last five to ten minutes and have occurred when walking uphill; the most recent episode began while carrying groceries and resolved after she stopped. She describes pressure rather than a sharp pain, with mild nausea and sweating during one episode. There is no current pain at assessment. She denies pain related to breathing, cough, fever, hemoptysis, recent trauma or unilateral leg swelling.

History includes hypertension and dyslipidemia, without known coronary disease, diabetes or previous venous thromboembolism. Her father had a myocardial infarction at age 54. She has never smoked and reports occasional alcohol use. Medications are losartan 50 mg daily and atorvastatin 20 mg nightly. She reports no known drug allergies. There has been no recent surgery, prolonged immobility or long-distance travel.

Observations: blood pressure 148/88 mmHg, heart rate 86/min and regular, respiratory rate 18/min, temperature 36.8°C and oxygen saturation 98% on room air. She is comfortable at rest and alert. Heart sounds are normal, lungs are clear, chest-wall palpation does not reproduce the discomfort, and there is no peripheral edema. An ECG has been requested but is not available in the note. Troponin results, previous ECGs and the precise relationship of every episode to exertion remain unknown.`},
    {label:'Abdominal pain', text:`31-year-old woman presenting with 18 hours of abdominal pain and nausea. Pain began near the umbilicus and is now more noticeable in the right lower abdomen. It has become constant and worsens with walking or coughing. She reports reduced appetite and one episode of non-bloody vomiting. Her last bowel movement yesterday was normal. She denies diarrhea, blood in stool, dysuria, flank pain or vaginal discharge. Her last menstrual period began approximately five weeks ago; usual cycles are 28 to 32 days, and pregnancy status is not yet established.

She has no previous abdominal operations, inflammatory bowel disease, kidney stones or known gynecologic conditions. Regular medication is an oral contraceptive, with two missed doses this month. She took one dose of paracetamol earlier today. She reports no known drug allergies, does not smoke and drinks alcohol occasionally. There has been no recent travel or unusual food exposure.

Observations: temperature 37.9°C, heart rate 102/min, blood pressure 116/72 mmHg, respiratory rate 18/min and oxygen saturation 99% on room air. She is alert and appears uncomfortable when moving. Examination notes right lower quadrant tenderness and localized guarding, without generalized rigidity. Urinalysis, pregnancy testing, blood count and imaging have not yet been completed. The note does not document a pelvic examination or a detailed sexual history.`}
  ];
  const medlineLink = code => 'https://connect.medlineplus.gov/application?mainSearchCriteria.v.cs=2.16.840.1.113883.6.90&mainSearchCriteria.v.c=' + encodeURIComponent(code) + '&informationRecipient.languageCode.c=en';
  const likelihoodBars = value => '<span class="likelihood-bars" aria-hidden="true">' + [1,2,3].map(n => `<i class="${n <= ({High:3,Moderate:2,Low:1}[value]) ? 'filled' : ''}"></i>`).join('') + '</span>';
  const icons = {
    check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    warning: '<path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5m0 3v.1"/>',
    upload: '<path d="M7 3h7l4 4v14H7zM14 3v5h4M12 17v-6m-3 3 3-3 3 3"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icons[name]}</svg>`;
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function say(text) { announcement.textContent = text; }
  function clearTimers() { timers.forEach(id => { clearTimeout(id); clearInterval(id); }); timers = []; }
  function setScreen(state, {focus = true, preserveDemo = false} = {}) {
    clearTimers(); if (!preserveDemo) { if (tour) stopTour(false); autoDemo = false; walkthrough = false; }
    current = state; stateSelect.value = state;
    document.body.classList.toggle('print-mode', state === 'print');
    if (['text', 'pdf', 'connection'].includes(state)) { if (state !== 'connection') mode = state; renderForm(state === 'connection'); }
    else if (['queued', 'processing'].includes(state)) renderProgress(state);
    else if (state === 'preparing') renderPreparing();
    else if (state === 'failed') renderFailure();
    else renderResults(state);
    if (focus) main.focus({preventScroll:true});
    say(`Preview: ${stateSelect.options[stateSelect.selectedIndex].text}`);
  }
  function renderForm(connection) {
    main.innerHTML = `<div class="page-head"><div><h1>New case</h1><p class="muted">Start with the clinical presentation.</p></div></div>
      <div class="submission"><section class="form-surface" aria-label="Case submission">
      ${connection ? `<div class="error-box" role="alert"><h2>${icon('warning')}Could not confirm submission</h2><p>The connection was interrupted. The request may have reached the service. Your case details are still here.</p><div class="actions"><button id="check-connection" type="button">Check connection</button></div><p id="connection-note" class="small"></p></div>` : ''}
      <section class="examples" aria-labelledby="examples-title"><h2 id="examples-title">Try an example case</h2><p>Not sure what to enter? Choose a fictional case to fill the form instantly.</p><div class="example-buttons">${examples.map((item,i)=>`<button type="button" data-example="${i}">${item.label}</button>`).join('')}</div></section><div class="mode-tabs" aria-label="Input method"><button type="button" data-mode="text" aria-pressed="${mode === 'text'}">Text entry</button><button type="button" data-mode="pdf" aria-pressed="${mode === 'pdf'}">PDF upload</button></div>
      <form id="case-form" novalidate>${mode === 'text' ? `<label class="field-label" for="case-text">Clinical summary</label><p id="text-hint" class="field-hint">Include the presenting concern, onset, observations and relevant history.</p><textarea id="case-text" maxlength="20000" aria-describedby="text-hint text-count form-error" placeholder="Age, symptoms, onset and duration, vital signs, history, medications and allergies…">${escape(draft)}</textarea><div class="field-meta"><span>At least 20 characters</span><span id="text-count">${draft.length.toLocaleString()} / 20,000</span></div>` : `<label class="field-label" for="case-file">Clinical note</label><p class="field-hint" id="file-hint">A text-based PDF, up to 10 MB. Scanned image PDFs are not supported.</p><div class="file-zone">${icon('upload')}<h2>Choose a PDF to review</h2><p class="small muted">This preview checks the file name and size only.</p><input id="case-file" type="file" accept="application/pdf,.pdf" aria-describedby="file-hint form-error"></div><div id="selected-file"></div>`}
      <p class="form-error" id="form-error" role="alert"></p><div class="form-actions">${mode === 'text' ? '<button type="button" class="text-button" id="load-sample">Load synthetic example</button>' : '<span class="small muted">The file stays on your device.</span>'}<button class="primary" type="submit">Preview analysis</button></div></form>
      <p class="inline-notice">Every submission opens the same fictional sample; entered text is not analyzed. This preview does not send cases.</p></section>
      <aside class="guidance"><h2>What to include</h2><section><h3>Presenting concern</h3><ul><li>Main symptoms and severity</li><li>Onset, duration and progression</li><li>Relevant symptoms that are absent</li></ul></section><section><h3>Observations</h3><ul><li>Vital signs</li><li>Examination findings</li><li>Available test results</li></ul></section><section><h3>Patient context</h3><ul><li>Age and relevant medical history</li><li>Current medications and allergies</li><li>Relevant exposures and risk factors</li></ul></section></aside></div>`;
    main.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => { mode = button.dataset.mode; setScreen(mode); }));
    main.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
      draft = examples[Number(button.dataset.example)].text; mode = 'text'; setScreen('text');
      document.getElementById('case-text').focus(); say(button.textContent + ' example loaded. Review or edit the text, then preview analysis.');
    }));
    const text = document.getElementById('case-text');
    if (text) {
      text.addEventListener('input', () => { draft = text.value; text.removeAttribute('aria-invalid'); document.getElementById('form-error').textContent = ''; document.getElementById('text-count').textContent = `${draft.length.toLocaleString()} / 20,000`; });
      document.getElementById('load-sample').addEventListener('click', () => { draft = sample; text.value = sample; text.dispatchEvent(new Event('input')); text.focus(); say('Synthetic example loaded.'); });
    } else {
      document.getElementById('case-file').addEventListener('change', e => { chosenFile = e.target.files[0] || null; showFile(); }); showFile();
    }
    document.getElementById('case-form').addEventListener('submit', e => {
      e.preventDefault(); const error = document.getElementById('form-error');
      if (mode === 'text' && draft.trim().length < 20) { error.textContent = 'Add at least 20 characters to preview a case.'; text.setAttribute('aria-invalid','true'); text.focus(); return; }
      if (mode === 'text' && draft.length > 20000) { error.textContent = 'Shorten the case to 20,000 characters.'; text.setAttribute('aria-invalid','true'); text.focus(); return; }
      if (mode === 'pdf' && !validFile()) return;
      autoDemo = !walkthrough; seconds = 0; setScreen('queued', {preserveDemo:true});
    });
    const check = document.getElementById('check-connection');
    if (check) check.addEventListener('click', () => { document.getElementById('connection-note').textContent = 'Simulation: connection restored. Submission status is still unknown; no new case was sent.'; check.disabled = true; say('Simulated connection restored. No new case submitted.'); });
  }
  function validFile() {
    let message = '';
    if (!chosenFile) message = 'Choose a PDF before continuing.';
    else if (!chosenFile.name.toLowerCase().endsWith('.pdf')) message = 'Choose a file with a .pdf extension.';
    else if (chosenFile.size > 10 * 1024 * 1024) message = 'The PDF must be 10 MB or smaller.';
    document.getElementById('form-error').textContent = message;
    document.getElementById('case-file').setAttribute('aria-invalid', String(Boolean(message)));
    return !message;
  }
  function showFile() {
    const area = document.getElementById('selected-file'); if (!area) return;
    document.getElementById('case-file').removeAttribute('aria-invalid');
    area.innerHTML = chosenFile ? `<div class="file-selected"><p><strong>${escape(chosenFile.name)}</strong><br><span class="small muted">${Math.ceil(chosenFile.size / 1024)} KB · Not uploaded</span></p><button type="button" id="remove-file">Remove</button></div>` : '';
    if (chosenFile) { validFile(); document.getElementById('remove-file').addEventListener('click', () => { chosenFile = null; document.getElementById('case-file').value = ''; showFile(); document.getElementById('form-error').textContent = ''; document.getElementById('case-file').focus(); }); }
  }
  function renderProgress(state) {
    const processing = state === 'processing', active = processing ? 2 : 1;
    const clock = '<svg class="icon state-symbol" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="18"/><path class="clock-hand" d="M22 9v13l8 5"/></svg>';
    const gear = '<svg class="icon state-symbol gear" viewBox="0 0 44 44" aria-hidden="true"><path d="m18 3 8 0 1 6 4 2 5-2 4 7-5 4v4l5 4-4 7-6-2-3 2-1 6h-8l-1-6-4-2-5 2-4-7 5-4v-4l-5-4 4-7 5 2 4-2z"/><circle cx="22" cy="22" r="7"/></svg>';
    main.innerHTML = `<section class="state-page"><ol class="timeline" aria-label="Analysis progress">${['Submitted','Queued','Analyzing','Ready'].map((label,i) => `<li class="${i < active ? 'complete' : i === active ? 'active' : ''}" ${i === active ? 'aria-current="step"' : ''}><span class="stage-dot">${i < active ? icon('check') : ''}</span>${label}</li>`).join('')}</ol><div class="stage-content">${processing ? gear : clock}<h1>${processing ? 'Analysis in progress' : 'Waiting for the analysis service'}</h1><p>${processing ? 'The case is being reviewed. The structured result will appear here when ready.' : 'Your case is queued. The worker may take a moment to wake up.'}</p><p class="small">This is a simulated workflow, not a live analysis.</p></div><div class="state-details"><dl><dt>Example job</dt><dd class="code">${jobId}</dd><dt>Elapsed</dt><dd id="elapsed" class="elapsed">00:00</dd></dl><button id="copy-result" type="button">Copy preview link</button></div><div class="state-actions"><button id="advance" type="button">${processing ? 'Show sample result' : 'Preview processing'}</button></div><p class="notice-line" id="action-notice" role="status"></p></section>`;
    const update = () => { const el = document.getElementById('elapsed'); if(el) el.textContent = `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`; };
    update(); timers.push(setInterval(() => { seconds++; update(); },1000));
    document.getElementById('advance').addEventListener('click', () => setScreen(processing ? 'results' : 'processing', {preserveDemo:walkthrough}));
    document.getElementById('copy-result').addEventListener('click', () => { const url = new URL(location.href); url.hash = 'results'; copy(url.href, 'Preview link copied.'); });
    if (autoDemo) timers.push(setTimeout(() => setScreen(processing ? 'results' : 'processing', {preserveDemo:true}), processing ? 4500 : 2500));
  }
  const conditions = [
    {name:'Pneumonia',likelihood:'High',code:'J18.9',verified:true,reason:'Fever, cough and progressive breathlessness are compatible with this possibility. Fever, hypoxemia and focal basal crackles support further evaluation; imaging and laboratory findings are not yet available.'},
    {name:'Pulmonary embolism',likelihood:'Moderate',code:'I26.99',verified:true,reason:'Breathlessness at rest warrants consideration of alternative explanations. The documented negative risk factors do not exclude this possibility; the available note does not establish a definitive cause.'},
    {name:'Acute bronchitis',likelihood:'Low',code:'J20.9',verified:false,reason:'Cough may fit a bronchial illness, but hypoxemia and focal crackles make an uncomplicated bronchial illness a less complete explanation. This example deliberately shows an unconfirmed terminology lookup.'}
  ];
  const extended = 'The documented observations and medical history narrow the questions for review, but do not establish the cause of the presentation. Chest imaging, laboratory testing and comparison with baseline function remain unavailable. The timing of any subsequent change in symptoms and repeat observations should be interpreted alongside the original examination. The display preserves this extended reasoning for review.';
  function renderResults(state) {
    const empty = state === 'empty', long = state === 'long';
    const list = empty ? [] : long ? [...conditions, {name:'Exacerbation of a pre-existing cardiopulmonary condition with an incompletely documented baseline',likelihood:'Low',code:'Not assigned',verified:false,reason:extended}] : conditions;
    main.innerHTML = `<div class="page-head"><div><h1>Case review</h1><div class="case-meta"><span>Completed · Synthetic example</span>${empty ? '<span class="urgency neutral">Urgency not available</span>' : ''}</div></div><div class="actions"><button id="copy-summary" type="button">Copy summary</button><button id="print-result" type="button">Print review</button></div></div><p class="notice-line" id="action-notice" role="status"></p>
      ${empty ? '' : `<section class="urgency-banner" aria-label="Clinical urgency"><h2>${icon('warning')}Urgent review</h2><p>Increasing breathlessness, now present at rest.</p><span>Illustrative urgency assessment · separate from diagnosis likelihood</span></section>`}<div class="workspace"><article class="report"><section class="summary"><h2>Patient summary</h2><p>${escape(sampleSummary)}${long ? ' '+extended : ''}</p></section><section class="differential"><div class="section-heading"><h2>Differential diagnosis${list.length ? ` (${list.length})` : ''}</h2><p>Model-assessed likelihood</p></div>${empty ? '<div class="empty-copy"><h3>No differential was returned</h3><p class="muted">An empty response is not a reassuring result. Review the input and try a new synthetic case.</p><button type="button" id="empty-new-case">Review a new case</button></div>' : list.map((c,i) => `<section class="condition"><div class="condition-head"><h3>${escape(c.name)}</h3><span class="likelihood ${c.likelihood.toLowerCase()}">${likelihoodBars(c.likelihood)}${c.likelihood} likelihood</span></div><div class="code-row">${c.code === 'Not assigned' ? `<span class="code">Not assigned</span>` : `<a class="code code-link" href="${escape(medlineLink(c.code))}" target="_blank" rel="noopener noreferrer" aria-label="${escape(c.code)}: related MedlinePlus information, opens in a new tab">${escape(c.code)}</a>`}<span class="${c.verified ? 'verified' : 'unverified'}">${c.verified ? icon('check')+' Code verified · NLM' : 'Code not verified'}</span></div><p>${escape(c.reason)}</p>${long && i < 3 ? `<details><summary>Read extended reasoning</summary><p>${extended}</p></details>` : ''}</section>`).join('')}</section><details class="code-help"><summary>What does code verification mean?</summary><p>A terminology lookup found the exact ICD-10-CM code. It does not confirm the diagnosis or its suitability for the case. All badges in this preview are illustrative.</p><p>Code links open related MedlinePlus patient education in a new tab. They are not exact coding guidance or diagnostic verification; a code may not have a matching article. Only the code is sent, never the case text.</p></details><section class="clinical-note"><h2>Clinical reasoning note</h2><p>${empty ? 'No clinical reasoning was returned in this example.' : 'Review these possibilities alongside the observations and missing information. The available details do not establish a diagnosis.'}</p></section><p class="report-meta">Example job <span class="code">${jobId}</span><br>Simulated result · Not a clinical assessment</p></article>
      <aside class="priorities" aria-label="Review priorities"><section class="priority-section flags"><h2>${icon('warning')}Red flags${empty ? '' : long ? ' (3)' : ' (1)'}</h2>${empty ? '<p>No red-flag assessment was returned. This does not establish absence of risk.</p>' : long ? '<ul><li>Increasing breathlessness, now present at rest.</li><li>Reported change in alertness; timing and context are unclear.</li><li>Reduced ability to perform usual daily activities.</li></ul>' : '<p>Increasing breathlessness, now present at rest.</p>'}</section><section class="priority-section next-section"><h2>Suggested next steps</h2>${empty ? '<p class="muted">No next steps were returned.</p>' : '<ol class="next-steps"><li>Review current observations and examination findings.</li><li>Clarify symptom onset, progression and associated features.</li><li>Review relevant history, medications and baseline function.</li></ol>'}</section><section class="priority-section missing"><h2>Missing information</h2>${empty ? '<p class="muted">No missing-information assessment was returned.</p>' : '<ul><li>Chest imaging</li><li>Blood count and renal function</li><li>Respiratory pathogen testing</li><li>Baseline oxygen saturation</li></ul>'}${long ? '<p>Long example: establish baseline daily function, any recent procedures, travel and exposures, and whether the reported change in alertness was observed directly or described by someone else.</p>' : ''}</section></aside></div>`;
    const workspace = main.querySelector('.workspace');
    workspace.prepend(workspace.querySelector('.flags'));
    document.getElementById('copy-summary').addEventListener('click', () => copy(reportText(list,empty,long), 'Review copied to clipboard.'));
    document.getElementById('print-result').addEventListener('click', () => { main.querySelectorAll('details').forEach(el => el.open = true); window.print(); });
    document.getElementById('empty-new-case')?.addEventListener('click', () => setScreen('text'));
    if (state === 'print') main.querySelectorAll('details').forEach(el => el.open = true);
  }
  function reportText(list,empty,long) {
    return ['Clinical case review — synthetic design example','Not a clinical assessment.',sample,'Urgency: '+(empty?'Not available':'Urgent (illustrative AI assessment)'),'Differential diagnosis',...list.map((c,i)=>`${c.name} — ${c.likelihood} likelihood — ${c.code} — ${c.verified?'Code verified (illustrative)':'Code not verified'}\n${c.reason}${long && i < 3?' '+extended:''}`),'Red flags: '+(empty?'Not returned':'Breathlessness at rest.'),'Suggested next steps: '+(empty?'Not returned':'Review observations; clarify onset; review history.'),'Missing information: '+(empty?'Not returned':'Chest imaging, blood count, renal function, respiratory pathogen testing and baseline oxygen saturation.'),'Clinical note: '+(empty?'Not returned':'Review possibilities alongside missing clinical information.'),'Code verification does not confirm a diagnosis.','Example job: '+jobId].join('\n\n');
  }
  function renderFailure() {
    main.innerHTML = `<section class="state-page"><div class="error-box"><h1>Analysis could not complete</h1><p>The simulated analysis service did not return a usable response.</p><p class="small">Example job <span class="code">${jobId}</span></p></div><p>The case has a failed status. Checking again retrieves this same job; it does not submit another case.</p><div class="state-actions"><button type="button" id="recheck">Check status</button><button type="button" class="primary" id="failed-new">Edit case</button></div><p id="action-notice" class="notice-line" role="status"></p></section>`;
    document.getElementById('recheck').addEventListener('click', () => { document.getElementById('action-notice').textContent = 'Simulation: this job still has a failed status. No new analysis was started.'; });
    document.getElementById('failed-new').addEventListener('click', () => setScreen('text'));
  }
  async function copy(text, success) {
    const target = document.getElementById('action-notice');
    try { if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable'); await navigator.clipboard.writeText(text); if(target) target.textContent=success; say(success); }
    catch { const message='Clipboard access is unavailable. Select and copy the visible review text instead.'; if(target) target.textContent=message; say(message); }
  }

  function renderPreparing() {
    main.innerHTML = `<section class="state-page preparing"><h1>Preparing the live demo</h1><p>The hosted services may need a moment to wake up after inactivity.</p><dl class="service-status"><dt>Analysis API</dt><dd>Waiting for a response</dd><dt>Background worker</dt><dd>Wake-up requested; processing not yet confirmed</dd></dl><p>This is a proposed startup screen. The design preview does not contact either service.</p><details><summary>Taking longer than expected?</summary><p>For the current deployed demo, open the worker page and leave it open until it responds, then return here. A response confirms the web process is awake; it does not prove the analysis worker is ready.</p><a href="https://cds-worker.onrender.com/" target="_blank" rel="noopener noreferrer">Open worker page (new tab)</a></details><div class="state-actions"><button type="button" id="prepared-next">Preview queued state</button><button type="button" id="prepared-back">Return to case</button></div></section>`;
    document.getElementById('prepared-next').addEventListener('click', () => setScreen('queued'));
    document.getElementById('prepared-back').addEventListener('click', () => setScreen('text'));
  }
  // The player owns its timers separately from the simulated analysis UI.
  const tourChrome = document.getElementById('tour-chrome');
  const demoCursor = document.getElementById('demo-cursor');
  const tourTitles = ['Choose a case', 'Read the clinical summary', 'Submit for analysis', 'Analysis in progress', 'Notice urgency', 'Compare diagnoses', 'Review next steps', 'Walkthrough complete'];
  let tourTasks = [], tourAnimations = [], cursorPosition = {x:80,y:160};
  function clearTourWork() {
    demoCursor.setAttribute('hidden','');
    tourTasks.forEach(task=>clearTimeout(task.id)); tourTasks=[];
    tourAnimations.forEach(animation=>animation.cancel()); tourAnimations=[];
    document.querySelectorAll('.tour-target').forEach(el=>el.classList.remove('tour-target'));
  }
  function later(fn,delay) {
    if(!tour) return;
    const task={fn,remaining:delay,due:performance.now()+delay,id:null};
    tourTasks.push(task);
    if(!tour.paused) arm(task);
  }
  function arm(task) {
    task.due=performance.now()+task.remaining;
    task.id=setTimeout(()=>{ tourTasks=tourTasks.filter(item=>item!==task); if(tour && !tour.paused) task.fn(); },task.remaining);
  }
  function pauseTour() {
    if(!tour || tour.paused) return;
    tour.paused=true;
    tourTasks.forEach(task=>{clearTimeout(task.id);task.remaining=Math.max(0,task.due-performance.now());});
    tourAnimations.filter(animation=>animation.playState === 'running').forEach(animation=>animation.pause());
    document.getElementById('tour-pause').textContent='Resume';
    document.body.classList.add('tour-paused');
  }
  function resumeTour() {
    if(!tour) return;
    tour.paused=false; tourTasks.forEach(arm); tourAnimations.filter(animation=>animation.playState === 'paused').forEach(animation=>animation.play());
    document.getElementById('tour-pause').textContent='Pause'; document.body.classList.remove('tour-paused');
  }
  function focusTourTarget(selector,click=false) {
    const element=main.querySelector(selector); if(!element) return;
    document.querySelectorAll('.tour-target').forEach(el=>el.classList.remove('tour-target'));
    element.classList.add('tour-target');
    const rect=element.getBoundingClientRect();
    const next={x:Math.min(innerWidth-44,Math.max(18,rect.left+rect.width*.65)),y:Math.min(innerHeight-100,Math.max(100,rect.top+Math.min(rect.height/2,34)))};
    if(!reducedMotion()) {
      demoCursor.removeAttribute('hidden');
      const animation=demoCursor.animate([{transform:`translate(${cursorPosition.x}px,${cursorPosition.y}px)`},{transform:`translate(${next.x}px,${next.y}px)`}],{duration:650,easing:'cubic-bezier(.16,1,.3,1)',fill:'forwards'});
      tourAnimations.push(animation); cursorPosition=next;
      if(click) later(()=>{
        const pulse=element.animate([{outlineOffset:'3px',outlineColor:'#235c91'},{outlineOffset:'9px',outlineColor:'transparent'}],{duration:450});
        tourAnimations.push(pulse);
      },650);
    }
  }
  function tourScroll(selector) {
    const target=main.querySelector(selector); if(!target) return;
    const offset=innerWidth<=760?140:95;
    window.scrollTo({top:Math.max(0,scrollY+target.getBoundingClientRect().top-offset),behavior:reducedMotion()?'instant':'smooth'});
  }
  function setTourScreen(state) {setScreen(state,{focus:false,preserveDemo:true});}
  function startTour() {
    if(tour) stopTour(false);
    tour={step:0,paused:reducedMotion(),saved:{draft,chosenFile,mode,current,scroll:scrollY}};
    walkthrough=true; autoDemo=false; seconds=0;
    tourChrome.hidden=false; document.body.classList.add('in-tour');
    document.body.classList.toggle('tour-paused',tour.paused);
    runTourStep(0); document.getElementById('tour-pause').focus({preventScroll:true});
  }
  function stopTour(render=true) {
    if(!tour) return;
    const saved=tour.saved; clearTourWork(); clearTimers(); tour=null; walkthrough=false; autoDemo=false;
    draft=saved.draft; chosenFile=saved.chosenFile; mode=saved.mode;
    tourChrome.hidden=true; demoCursor.setAttribute('hidden',''); document.body.classList.remove('in-tour','tour-paused');
    if(render) {setScreen(saved.current); window.scrollTo({top:saved.scroll,behavior:'instant'});}
  }
  function runTourStep(index) {
    if(!tour) return;
    clearTourWork(); tour.step=index; walkthrough=true; autoDemo=false;
    document.getElementById('tour-step').textContent=`${index+1} / ${tourTitles.length} · ${tourTitles[index]}`;
    document.getElementById('tour-caption').textContent=[
      'The cursor selects a ready-to-use clinical case.',
      'Review the symptoms, observations, history and medications before submitting.',
      'The case is submitted once and joins the analysis queue.',
      'The worker organizes the case into a structured review.',
      'Urgency and red flags are separate from diagnosis likelihood.',
      'Compare the possibilities and inspect the linked ICD-10 codes.',
      'Review suggested next steps and the information still needed.',
      'You have seen the complete workflow. Exit to try a case yourself.'
    ][index];
    document.getElementById('tour-next').textContent=index===7?'Replay':'Next step';
    document.getElementById('tour-pause').hidden=index===7;
    document.getElementById('tour-pause').textContent=tour.paused?'Resume':'Pause';
    const wait=[2200,6500,3600,3200,4200,5000,5000,0][index];
    if(index===0) {
      draft=''; mode='text'; setTourScreen('text'); window.scrollTo({top:0,behavior:'instant'});
      focusTourTarget('[data-example="0"]',true);
    } else if(index===1) {
      draft=sample; mode='text'; setTourScreen('text'); tourScroll('#case-text');
      later(()=>focusTourTarget('#case-text'),450);
      later(()=>{const input=document.getElementById('case-text'); if(input) input.scrollTop=input.scrollHeight;},3500);
    } else if(index===2) {
      draft=sample; mode='text'; setTourScreen('text'); tourScroll('.form-actions');
      if(tour.paused) {setTourScreen('queued');window.scrollTo({top:0,behavior:'instant'});}
      else later(()=>focusTourTarget('button[type="submit"]',true),450);
      if(!tour.paused) later(()=>{document.getElementById('case-form')?.requestSubmit(); window.scrollTo({top:0,behavior:'instant'});demoCursor.setAttribute('hidden','');},1450);
    } else if(index===3) {
      setTourScreen('processing'); window.scrollTo({top:0,behavior:'instant'}); demoCursor.setAttribute('hidden','');
    } else {
      setTourScreen('results');
      const selector=index===4?'.urgency-banner':index===5?'.differential':index===6?'.next-section':'.page-head';
      tourScroll(selector); later(()=>focusTourTarget(selector),450);
      if(index===7) {demoCursor.setAttribute('hidden','');pauseTour();}
    }
    if(wait) later(()=>runTourStep(index+1),wait);
    say(`Walkthrough step ${index+1}: ${tourTitles[index]}`);
  }
  document.getElementById('tour-pause').addEventListener('click',()=>tour?.paused?resumeTour():pauseTour());
  document.getElementById('tour-next').addEventListener('click',()=>{if(!tour)return;if(tour.step===7){tour.paused=reducedMotion();document.body.classList.toggle('tour-paused',tour.paused);runTourStep(0);}else runTourStep(tour.step+1);});
  document.getElementById('tour-exit').addEventListener('click',()=>stopTour());
  // Visitors can pause by interacting; real clicks never trigger a second analysis.
  main.addEventListener('click',event=>{if(tour && event.isTrusted){event.preventDefault();event.stopImmediatePropagation();pauseTour();}},true);
  main.addEventListener('keydown',event=>{if(tour && event.isTrusted && event.key!=='Tab'){event.preventDefault();pauseTour();}},true);
  window.addEventListener('wheel',()=>{if(tour)pauseTour();},{passive:true});
  window.addEventListener('touchstart',event=>{if(tour && !event.target.closest('#tour-chrome'))pauseTour();},{passive:true});
  window.addEventListener('resize',()=>{if(tour){pauseTour();demoCursor.setAttribute('hidden','');}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden && tour)pauseTour();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape' && tour)stopTour();});
  const welcome = document.getElementById('welcome-dialog');
  let miniTimers = [], invitationInteracted = false, welcomeReturnFocus = null, welcomeDestination = null;

  function stopMini() { miniTimers.forEach(clearTimeout); miniTimers = []; }
  function miniFrame(step) {
    welcome.querySelectorAll('[data-mini-step]').forEach(el => el.classList.toggle('active', Number(el.dataset.miniStep) === step));
    document.getElementById('mini-content').innerHTML = [
      '<div class="mini-queue"><span class="mini-clock" aria-hidden="true"></span><strong>Case received</strong><p>Waiting for the analysis worker</p></div>',
      '<div class="mini-queue"><span class="mini-analysis" aria-hidden="true"></span><strong>Reviewing the case</strong><p>Organizing the clinical information</p></div>',
      '<div class="mini-results"><div><strong>Differential diagnosis</strong><p>Pneumonia <span>High likelihood</span></p><p>Pulmonary embolism <span>Moderate likelihood</span></p></div><div><strong>Review priorities</strong><p class="mini-flag">Red flags</p><p>Suggested next steps</p><p>Missing information</p></div></div>'
    ][step];
  }
  function playMini() {
    stopMini(); miniFrame(0);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { miniFrame(2); return; }
    miniTimers.push(setTimeout(()=>miniFrame(1),1300),setTimeout(()=>miniFrame(2),2800));
  }
  function openWelcome() {
    if(welcome.open) return; if(tour) stopTour();
    welcomeReturnFocus = document.activeElement; welcomeDestination = null; welcome.showModal();
    const source = document.getElementById('how-it-works').getBoundingClientRect();
    const destination = welcome.getBoundingClientRect();
    if (!reducedMotion()) welcome.animate([
      {transform:`translate(${source.left + source.width/2 - destination.left - destination.width/2}px, ${source.top + source.height/2 - destination.top - destination.height/2}px) scale(${source.width/destination.width}, ${source.height/destination.height})`, opacity:.2},
      {transform:'translate(0,0) scale(1)',opacity:1}
    ], {duration:450,easing:'cubic-bezier(.16,1,.3,1)'});
    playMini();
  }
  function closeWelcome() { welcome.close(); }
  welcome.addEventListener('close', () => {
    stopMini();
    if (welcomeDestination === 'walkthrough') startTour();
    else if (welcomeReturnFocus?.isConnected) welcomeReturnFocus.focus();
    welcomeDestination = null;
  });
  document.getElementById('how-it-works').addEventListener('click',openWelcome);
  document.getElementById('close-welcome').addEventListener('click',closeWelcome);
  document.getElementById('skip-welcome').addEventListener('click',closeWelcome);
  document.getElementById('replay-mini').addEventListener('click',playMini);
  document.getElementById('start-walkthrough').addEventListener('click',()=>{ welcomeDestination = 'walkthrough'; closeWelcome(); });
  ['pointerdown','keydown','input'].forEach(event => document.addEventListener(event,()=>{invitationInteracted=true;},{once:true,capture:true}));

  stateSelect.addEventListener('change', () => { seconds=0; setScreen(stateSelect.value); });
  document.getElementById('navy-header').addEventListener('change', e => document.body.classList.toggle('navy',e.target.checked));
  document.getElementById('new-case').addEventListener('click', () => { if(tour) stopTour(false); draft = ''; chosenFile = null; setScreen('text'); });
  document.getElementById('brand-link').addEventListener('click', e => { e.preventDefault(); setScreen('text'); });
  window.addEventListener('beforeunload',clearTimers);
  const initial=location.hash.slice(1); setScreen([...stateSelect.options].some(o=>o.value===initial)?initial:'text',{focus:false});
  if(!initial) setTimeout(()=>{ if(!invitationInteracted && current === 'text') openWelcome(); },800);
})();
