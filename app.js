let papers=[];
const list=document.querySelector('#paperList');
const search=document.querySelector('#search');
const field=document.querySelector('#fieldFilter');
const count=document.querySelector('#resultCount');

function escapeHtml(value){return String(value||'').replace(/[&<>'"]/g,character=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));}

function render(){
  const query=search.value.toLowerCase().trim();
  const shown=papers.filter(paper=>(field.value==='all'||paper.field===field.value)&&[paper.title,paper.authors,paper.journal,JSON.stringify(paper.summary)].join(' ').toLowerCase().includes(query));
  count.textContent=`${shown.length} paper${shown.length===1?'':'s'}`;
  list.innerHTML=shown.length?shown.map(paper=>`<article class="paper"><h2><a href="${escapeHtml(paper.url)}" target="_blank" rel="noreferrer">${escapeHtml(paper.title)}</a></h2><p class="metadata">${escapeHtml(paper.authors)} · ${escapeHtml(paper.journal)} · ${escapeHtml(paper.year)}</p><p class="summary"><strong>AI summary:</strong> <b>Goal:</b> ${escapeHtml(paper.summary?.goal)} <b>Methodology:</b> ${escapeHtml(paper.summary?.methodology)} <b>Finding:</b> ${escapeHtml(paper.summary?.finding)}</p></article>`).join(''):'<p class="empty">No papers match this search yet.</p>';
}

function renderBars(container,items,labelKey){
  const maximum=Math.max(...items.map(item=>item.count),1);
  container.innerHTML=items.length?items.map(item=>`<div class="bar-row"><span>${escapeHtml(item[labelKey])}</span><div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:${(item.count/maximum)*100}%"></div></div><b>${item.count}</b></div>`).join(''):'<p class="empty">No trend data yet.</p>';
}

function renderInsights(insights){
  document.querySelector('#insightsUpdated').textContent=insights.updatedAt?`Based on ${insights.paperCount} papers · updated ${new Date(insights.updatedAt).toUTCString().replace('GMT','UTC')}`:'Insights will update with the first paper run.';
  document.querySelector('#corpusSummary').textContent=insights.corpusSummary||'';
  document.querySelector('#themes').innerHTML=(insights.themes||[]).map(theme=>`<article class="theme"><h4>${escapeHtml(theme.name)}</h4><p>${escapeHtml(theme.description)}</p></article>`).join('')||'<p class="empty">Themes will appear after the first corpus analysis.</p>';
  document.querySelector('#keywords').innerHTML=(insights.emergingKeywords||[]).map(keyword=>`<span>${escapeHtml(keyword)}</span>`).join('')||'<p class="empty">No keywords yet.</p>';
  renderBars(document.querySelector('#yearTrend'),insights.yearCounts||[],'year');
  renderBars(document.querySelector('#fieldTrend'),insights.fieldCounts||[],'field');
}

async function load(){
  try{
    const [paperData,insights]=await Promise.all([
      fetch('data/papers.json').then(response=>response.json()),
      fetch('data/insights.json').then(response=>response.ok?response.json():null),
    ]);
    papers=paperData.papers||[];
    document.querySelector('#updatedAt').textContent=paperData.updatedAt?`Updated ${new Date(paperData.updatedAt).toUTCString().replace('GMT','UTC')}.`:'Updated daily.';
    [...new Set(papers.map(paper=>paper.field).filter(Boolean))].sort().forEach(name=>field.insertAdjacentHTML('beforeend',`<option>${escapeHtml(name)}</option>`));
    if(insights)renderInsights(insights);
    render();
  }catch{list.innerHTML='<p class="empty">The paper dataset could not be loaded.</p>';}
}

search.addEventListener('input',render);
field.addEventListener('change',render);
load();
