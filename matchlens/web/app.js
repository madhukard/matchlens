const $ = (id) => document.getElementById(id);
const state = { audience: 'fan', language: 'en', start: 3300, end: 3900, data: null, selected: null, timer: null, request: 0 };
const embedded = window.parent !== window;
const pending = new Map();
let rpcId = 0;
let hostReady = false;
const fmt = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
const labels = { en: { pass: 'Pass', recovery: 'Recovery', shot: 'Shot', goal: 'Goal' }, es: { pass: 'Pase', recovery: 'Recuperación', shot: 'Disparo', goal: 'Gol' } };
function rpc(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++rpcId;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error('The host did not respond. Please reconnect the MatchLens app.')); }, 12000);
    pending.set(id, { resolve, reject, timeout });
    window.parent.postMessage({ jsonrpc: '2.0', id, method, params }, '*');
  });
}
function notify(method, params) { if (hostReady) window.parent.postMessage({ jsonrpc: '2.0', method, params }, '*'); }
function hostContext(ctx) {
  if (!ctx) return;
  if (ctx.theme) document.documentElement.style.colorScheme = ctx.theme;
  for (const [key, value] of Object.entries(ctx.styles?.variables || {})) {
    if (key.startsWith('--') && typeof value === 'string') document.documentElement.style.setProperty(key, value);
  }
  if (ctx.safeAreaInsets) for (const [side, value] of Object.entries(ctx.safeAreaInsets)) {
    if (['top','bottom','left','right'].includes(side) && Number.isFinite(value)) document.body.style.setProperty(`padding-${side}`, `${value}px`);
  }
}
window.addEventListener('message', (event) => {
  if (!embedded || event.source !== window.parent || event.data?.jsonrpc !== '2.0') return;
  const message = event.data;
  if (pending.has(message.id)) {
    const item = pending.get(message.id); clearTimeout(item.timeout); pending.delete(message.id);
    if (message.error) item.reject(new Error(message.error.message)); else item.resolve(message.result);
  } else if (message.method === 'ui/notifications/tool-result' && message.params?.structuredContent?.match) {
    accept(message.params.structuredContent);
  } else if (message.method === 'ui/notifications/host-context-changed') hostContext(message.params);
});
async function tool(name, args) {
  let result;
  if (embedded) result = await rpc('tools/call', { name, arguments: args });
  else {
    const response = await fetch('/api/tools', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, arguments: args }) });
    if (!response.ok) throw new Error(`Match service returned ${response.status}. Please try again.`);
    result = await response.json();
  }
  if (result.isError) throw new Error(result.content?.[0]?.text || 'Tool could not complete.');
  return result.structuredContent;
}
function showError(error) { $('error').hidden = false; $('error').textContent = error.message || String(error); }
async function load() {
  const request = ++state.request;
  $('error').hidden = true;
  stop();
  try {
    const data = await tool('explain_moment', { match_id: 'harbor-summit-demo', start_second: state.start, end_second: state.end, audience: state.audience, language: state.language });
    if (request === state.request) accept(data);
  } catch (error) { if (request === state.request) showError(error); }
}
function accept(data) {
  if (!data?.match || !Array.isArray(data.events)) return;
  stop(); state.data = data; state.start = data.window.start_second; state.end = data.window.end_second;
  if (data.insight) { state.audience = data.insight.audience; state.language = data.insight.language; }
  $('language').value = state.language;
  document.documentElement.lang = state.language;
  for (const mode of ['fan','analyst']) { $(mode).classList.toggle('active', mode === state.audience); $(mode).setAttribute('aria-pressed', String(mode === state.audience)); }
  $('score').textContent = `${data.score.harbor} : ${data.score.summit}`;
  $('match-clock').textContent = `${Math.floor(state.end/60)}′ · REPLAY SNAPSHOT`;
  $('window-title').textContent = state.start === 0 ? 'The whole match' : `${Math.floor(state.start/60)}–${Math.floor(state.end/60)}′ · The turning point`;
  const insight = data.insight;
  $('source').textContent = insight?.source === 'agents_sdk' ? 'AI narrative · evidence reviewed' : 'Statistics only · AI not generated';
  $('headline').textContent = insight?.narrative.headline || 'Explore the match';
  $('summary').textContent = insight?.narrative.summary || 'Select an event to inspect its evidence.';
  $('uncertainty').textContent = insight?.analysis?.uncertainty || '';
  $('uncertainty').hidden = !$('uncertainty').textContent;
  $('metrics').replaceChildren();
  const metrics = state.audience === 'fan' ? [['shots','Shots'],['high_recoveries','High recoveries'],['goals','Goals in window']] : [['completed_passes','Completed passes'],['pass_accuracy','Pass accuracy %'],['progressive_passes','Progressive passes']];
  for (const [key,label] of metrics) {
    const block = document.createElement('div'); block.className = 'metric';
    const caption = document.createElement('span'); caption.textContent = label;
    const number = document.createElement('strong'); number.textContent = `${data.stats.harbor[key] ?? '—'} / ${data.stats.summit[key] ?? '—'}`;
    const legend = document.createElement('small'); legend.textContent = 'Harbor / Summit';
    block.append(caption,number,legend); $('metrics').append(block);
  }
  const oldPlayer = $('player').value; $('player').replaceChildren(new Option('All players','all'));
  for (const player of [...new Set(data.events.map(e=>e.player))].sort()) $('player').add(new Option(player,player));
  $('player').value = [...$('player').options].some(o=>o.value===oldPlayer) ? oldPlayer : 'all';
  $('time').min = state.start; $('time').max = state.end-1; $('time').value = state.end-1;
  const ids = new Set(insight?.narrative.evidence_event_ids || []);
  const evidence = data.events.filter(e=>ids.has(e.event_id));
  $('evidence-count').textContent = String(evidence.length);
  $('evidence-list').replaceChildren();
  for (const event of evidence.slice(0,6)) $('evidence-list').append(eventButton(event, true));
  if (!evidence.length) { const note=document.createElement('p'); note.className='muted'; note.textContent='No reviewed narrative for this window. Browse the events below.'; $('evidence-list').append(note); }
  $('show-evidence').disabled = !evidence.length;
  state.selected = evidence[0] || data.events.at(-1) || null;
  renderEvents(); updateContext();
}
function eventButton(event, evidence = false) {
  const button = document.createElement('button'); button.className = evidence ? 'evidence-item' : '';
  button.dataset.id = event.event_id;
  const minute = document.createElement('strong'); minute.textContent = fmt(event.second);
  const caption = document.createElement('span'); caption.textContent = `${labels[state.language][event.kind]} · ${event.player}`;
  const id = document.createElement('small'); id.textContent = event.event_id;
  caption.append(id); button.append(minute,caption);
  button.addEventListener('click',()=>{ state.selected=event; $('time').value=event.second; draw(); updateContext(); });
  return button;
}
function renderEvents() {
  const visible=state.data.events.filter(e=>$('player').value==='all'||e.player===$('player').value);
  $('timeline').replaceChildren(...visible.map(e=>eventButton(e)));
  $('event-count').textContent=`${visible.length} recorded events`;
  if (state.selected && !visible.includes(state.selected)) state.selected=visible[0]||null;
  draw();
}
function svgElement(name, attrs) { const node=document.createElementNS('http://www.w3.org/2000/svg',name); for(const [key,value] of Object.entries(attrs)) node.setAttribute(key,String(value)); return node; }
function draw() {
  const time=Number($('time').value); $('time-label').textContent=fmt(time);
  $('event-trails').replaceChildren(); $('active-event').replaceChildren();
  const visible=state.data.events.filter(e=>e.second<=time&&($('player').value==='all'||e.player===$('player').value));
  for (const event of visible.slice(-18)) {
    const color=event.team==='harbor'?'#e3f3b0':'#f1bc72';
    $('event-trails').append(svgElement('circle',{cx:event.x,cy:event.y,r:.75,fill:color,opacity:.4}));
  }
  const event=state.selected?.second<=time ? state.selected : visible.at(-1);
  if(event) {
    const color=event.team==='harbor'?'#e3f3b0':'#f1bc72';
    const group=$('active-event');
    group.append(svgElement('line',{x1:event.x,y1:event.y,x2:event.end_x,y2:event.end_y,stroke:color,'stroke-width':.75,'stroke-dasharray':event.successful?'none':'2 1'}));
    group.append(svgElement('circle',{cx:event.x,cy:event.y,r:2.3,fill:color,stroke:'#163d31','stroke-width':.5}));
    group.append(svgElement('circle',{cx:event.end_x,cy:event.end_y,r:1,fill:color}));
    const text=svgElement('text',{x:event.x,y:event.y-4,fill:'#fff','font-size':2.8,'text-anchor':'middle'}); text.textContent=event.player;group.append(text);
    $('event-caption').textContent=`${fmt(event.second)} · ${labels[state.language][event.kind]} · ${event.player}${event.successful?'':' · incomplete'}`;
  } else $('event-caption').textContent='No events at this point in the selected window';
  for(const button of $('timeline').querySelectorAll('button')) button.classList.toggle('selected',button.dataset.id===event?.event_id);
}
function updateContext() { if (!hostReady) return; rpc('ui/update-model-context',{structuredContent:{match_id:'harbor-summit-demo',window:{start_second:state.start,end_second:state.end},audience:state.audience,language:state.language,selected_event_id:state.selected?.event_id||null}}).catch(()=>{}); }
function stop(){clearInterval(state.timer);state.timer=null;$('play').textContent='▶';$('play').setAttribute('aria-label','Play event replay');}
$('play').addEventListener('click',()=>{
  if(state.timer){stop();return;}
  if(!state.data)return;
  if(Number($('time').value)>=state.end-1)$('time').value=state.start;
  state.selected=null;$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','Pause event replay');
  state.timer=setInterval(()=>{ $('time').value=Math.min(state.end-1,Number($('time').value)+15);draw();if(Number($('time').value)>=state.end-1)stop();},350);
});
$('time').addEventListener('input',()=>{stop();state.selected=null;draw();});
$('player').addEventListener('change',()=>{renderEvents();updateContext();});
$('show-evidence').addEventListener('click',()=>{const id=state.data.insight.narrative.evidence_event_ids[0];state.selected=state.data.events.find(e=>e.event_id===id);$('time').value=state.selected.second;draw();updateContext();});
for(const mode of ['fan','analyst'])$(mode).addEventListener('click',()=>{state.audience=mode;load();});
$('language').addEventListener('change',()=>{state.language=$('language').value;load();});
$('recap').addEventListener('click',()=>{state.start=0;state.end=5400;load();});
$('reset-window').addEventListener('click',()=>{state.start=3300;state.end=3900;load();});
window.addEventListener('pagehide',stop);
async function start(){
  if(embedded){
    try{const init=await rpc('ui/initialize',{appInfo:{name:'matchlens',version:'0.1.0'},appCapabilities:{},protocolVersion:'2026-01-26'});hostReady=true;hostContext(init.hostContext);notify('ui/notifications/initialized',{});if(!state.data)await load();}
    catch(error){showError(error);}
  }else await load();
}
start();

new ResizeObserver(() => notify('ui/notifications/size-changed', {height: document.documentElement.scrollHeight})).observe(document.body);
