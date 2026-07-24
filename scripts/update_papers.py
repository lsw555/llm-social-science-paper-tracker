"""Discover, screen, and summarize recent social-science research about LLMs."""
import json, os, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'papers.json'; KEY=os.environ['OPENAI_API_KEY']
QUERIES=[
    '"large language model" public opinion',
    'ChatGPT "content analysis" social science',
    '"generative AI" "human AI interaction"',
    'ChatGPT mental health empathy support',
    'AI generated news perception credibility',
    '"large language model" human behavior bias',
    'LLM climate behavior communication',
]
SYSTEM='''You are screening academic papers for an LLM social science tracker. Return ONLY JSON.

Include a paper only if it substantively concerns large language models, ChatGPT, or generative AI and belongs to at least one of these streams:
1. AI AS A SOCIAL-SCIENCE RESEARCH TOOL: using LLMs to predict or simulate public opinion, analyze text/content, classify social data, conduct surveys/experiments, or otherwise improve social-science research.
2. HUMAN–AI INTERACTION AND SOCIAL OUTCOMES: how people interact with AI and effects on attitudes, trust, wellbeing/mental health, social support, health or climate behaviors, learning, work, communication, or perceptions of AI-generated news/media.
3. LLM BEHAVIOR AS A SOCIAL PHENOMENON: whether LLM responses resemble human behavior, attitudes, values, cognition, stereotypes, discrimination, political bias, or other human biases.

Exclude papers that only improve model architecture, benchmarks, coding, mathematics, hardware, or generic technical performance. Also exclude papers that merely use AI without studying one of the three streams.

For an included paper, choose exactly one field from: "AI as research tool", "Human–AI interaction", "Health & wellbeing", "Media & communication", "Public opinion & politics", "Climate & environment", "Work & education", "LLM behavior & bias". Provide a simple summary with goal, methodology, and finding. Each value must be one sentence, grounded only in the abstract; if a result is not reported, say "The abstract does not report findings." Schema: {"include":boolean,"field":string,"goal":string,"methodology":string,"finding":string}.'''
def get_json(url,headers=None):
    with urlopen(Request(url,headers=headers or {}),timeout=60) as r:return json.load(r)
def abstract(work):
    words=work.get('abstract_inverted_index') or {}; ordered=sorted(((i,w) for w,positions in words.items() for i in positions)); return ' '.join(w for _,w in ordered)
def text_response(prompt):
    payload=json.dumps({'model':'gpt-5.6-luna','input':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],'text':{'verbosity':'low'}}).encode()
    result=get_json('https://api.openai.com/v1/responses',{'Authorization':f'Bearer {KEY}','Content-Type':'application/json'}) if False else None
    request=Request('https://api.openai.com/v1/responses',data=payload,method='POST',headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'})
    with urlopen(request,timeout=90) as r:return json.load(r)['output_text']
def authors(work): return ', '.join(a['author']['display_name'] for a in work.get('authorships',[])[:8]) or 'Author unavailable'
def main():
    existing=json.loads(DATA.read_text()); seen={p['id'] for p in existing.get('papers',[]) if p.get('id')}; since=(datetime.now(timezone.utc)-timedelta(days=10)).date().isoformat(); candidates=[]
    for query in QUERIES:
        url='https://api.openalex.org/works?'+urlencode({'search':query,'filter':f'from_publication_date:{since},has_abstract:true','per-page':25,'sort':'publication_date:desc','select':'id,doi,title,publication_year,publication_date,authorships,primary_location,abstract_inverted_index'})
        candidates.extend(get_json(url).get('results',[]))
    for work in candidates:
        if work['id'] in seen or not work.get('title'): continue
        abs_text=abstract(work)
        if not abs_text: continue
        try: verdict=json.loads(re.search(r'\{.*\}',text_response(f"Title: {work['title']}\nAbstract: {abs_text}"),re.S).group())
        except Exception as error: print(f"Skipping {work['id']}: {error}"); continue
        if not verdict.get('include'): continue
        source=((work.get('primary_location') or {}).get('source') or {}).get('display_name') or 'Venue unavailable'
        existing['papers'].append({'id':work['id'],'title':work['title'],'authors':authors(work),'journal':source,'year':work.get('publication_year','Year unavailable'),'field':verdict['field'],'url':work.get('doi') or work['id'],'summary':{k:verdict[k] for k in ('goal','methodology','finding')}}); seen.add(work['id'])
    existing['papers'].sort(key=lambda p:(str(p['year']),p['title']),reverse=True); existing['updatedAt']=datetime.now(timezone.utc).isoformat(); DATA.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
