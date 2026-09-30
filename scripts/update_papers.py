"""Discover, screen, and summarize recent social-science research about LLMs."""
import json, os, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from time import sleep

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'papers.json'; KEY=os.environ['OPENAI_API_KEY']
QUERIES=[
    '"large language model" social science',
    '"generative AI" social science',
    '"large language model" public opinion',
    '"large language model" "content analysis"',
    '"large language model" communication media journalism',
    '"large language model" "human AI interaction"',
    '"generative AI" mental health empathy social support',
    '"generative AI" health behavior climate behavior',
    '"AI generated news" perception credibility',
    '"large language model" human behavior bias',
    '"large language model" values stereotypes discrimination',
]
MAX_NEW_PAPERS=10
# OpenAlex can rate-limit requests originating from shared GitHub Actions IP
# addresses.  Spread the searches out and retry temporary rate-limit/network
# failures instead of failing the entire daily update.
OPENALEX_REQUEST_DELAY_SECONDS=1.0
OPENALEX_MAX_RETRIES=5
# Strict journal whitelist. Values are normalized to handle punctuation differences
# in OpenAlex metadata (for example, "PNAS" versus the journal's full title).
ALLOWED_JOURNALS={
    'humanitiesandsocialsciencescommunications',
    'scientificreports',
    'naturecommunications',
    'nature',
    'science',
    'computersinhumanbehavior',
    'socialsciencecomputerreview',
    'pnas',
    'proceedingsofthenationalacademyofsciences',
    'pnasnexus',
    'digitaljournalism',
    'journalofcommunication',
    'communicationresearch',
    'humancommunicationresearch',
    'communicationmethodsandmeasures',
}
PREFILTER_SYSTEM='''You are the first, conservative screening pass for an LLM social science paper tracker. Return ONLY {"candidate": true} or {"candidate": false}.

Return true when the paper might substantively concern LLMs, ChatGPT, or generative AI in at least one of these areas: (1) LLMs as a social-science research tool such as public-opinion prediction, simulation, or content analysis; (2) human–AI interaction and social outcomes such as trust, mental health, support, health or climate behavior, learning, work, or AI-generated news; or (3) whether LLM behavior resembles human attitudes, values, cognition, stereotypes, or bias.

Return false only for clearly unrelated or purely technical architecture, benchmark, coding, mathematics, hardware, or generic performance papers. When uncertain, return true for final review.'''
FINAL_SYSTEM='''You are the final screening pass for an LLM social science tracker. Return ONLY JSON.

Include a paper only if it substantively concerns large language models, ChatGPT, or generative AI and belongs to at least one of these streams:
1. AI AS A SOCIAL-SCIENCE RESEARCH TOOL: using LLMs to predict or simulate public opinion, analyze text/content, classify social data, conduct surveys/experiments, or otherwise improve social-science research.
2. HUMAN–AI INTERACTION AND SOCIAL OUTCOMES: how people interact with AI and effects on attitudes, trust, wellbeing/mental health, social support, health or climate behaviors, learning, work, communication, or perceptions of AI-generated news/media.
3. LLM BEHAVIOR AS A SOCIAL PHENOMENON: whether LLM responses resemble human behavior, attitudes, values, cognition, stereotypes, discrimination, political bias, or other human biases.

Exclude papers that only improve model architecture, benchmarks, coding, mathematics, hardware, or generic technical performance. Also exclude papers that merely use AI without studying one of the three streams.

For an included paper, choose exactly one field from: "AI as research tool", "Human–AI interaction", "Health & wellbeing", "Media & communication", "Public opinion & politics", "Climate & environment", "Work & education", "LLM behavior & bias". Provide a simple summary with goal, methodology, and finding. Each value must be one sentence, grounded only in the abstract; if a result is not reported, say "The abstract does not report findings." Schema: {"include":boolean,"field":string,"goal":string,"methodology":string,"finding":string}.'''
def get_json(url,headers=None):
    request_headers={
        'User-Agent':'LLM-Social-Science-Paper-Tracker/1.0 (https://github.com/lsw555/llm-social-science-paper-tracker)'
    }
    request_headers.update(headers or {})
    for attempt in range(OPENALEX_MAX_RETRIES):
        try:
            with urlopen(Request(url,headers=request_headers),timeout=60) as response:
                payload=json.load(response)
            sleep(OPENALEX_REQUEST_DELAY_SECONDS)
            return payload
        except HTTPError as error:
            if error.code != 429 or attempt == OPENALEX_MAX_RETRIES - 1:
                raise
            retry_after=error.headers.get('Retry-After')
            try:
                wait_seconds=float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                wait_seconds=2 ** attempt
            print(f'OpenAlex rate-limited the request; retrying in {wait_seconds:.0f} seconds ({attempt + 1}/{OPENALEX_MAX_RETRIES}).', flush=True)
            sleep(wait_seconds)
        except URLError as error:
            if attempt == OPENALEX_MAX_RETRIES - 1:
                raise
            wait_seconds=2 ** attempt
            print(f'OpenAlex request failed ({error.reason}); retrying in {wait_seconds:.0f} seconds ({attempt + 1}/{OPENALEX_MAX_RETRIES}).', flush=True)
            sleep(wait_seconds)
def abstract(work):
    words=work.get('abstract_inverted_index') or {}; ordered=sorted(((i,w) for w,positions in words.items() for i in positions)); return ' '.join(w for _,w in ordered)
def normalise(value): return re.sub(r'[^a-z0-9]+','',str(value).lower())
def source_name(work): return ((work.get('primary_location') or {}).get('source') or {}).get('display_name') or ''
def allowed_journal(name): return normalise(name) in ALLOWED_JOURNALS
def text_response(model, instructions, prompt):
    payload=json.dumps({'model':model,'input':[{'role':'system','content':instructions},{'role':'user','content':prompt}],'text':{'verbosity':'low'}}).encode()
    request=Request('https://api.openai.com/v1/responses',data=payload,method='POST',headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'})
    with urlopen(request,timeout=90) as r: response=json.load(r)
    for item in response.get('output',[]):
        if item.get('type') != 'message': continue
        for content in item.get('content',[]):
            if content.get('type') == 'output_text': return content['text']
    raise ValueError('The OpenAI response did not contain output text.')
def authors(work): return ', '.join(a['author']['display_name'] for a in work.get('authorships',[])[:8]) or 'Author unavailable'
def main():
    existing=json.loads(DATA.read_text())
    # Keep the public catalogue consistent with the whitelist, including papers
    # collected before the restriction was introduced.
    papers=[paper for paper in existing.get('papers',[]) if allowed_journal(paper.get('journal',''))]
    existing['papers']=papers
    seen_ids={p['id'] for p in papers if p.get('id')}; seen_dois={normalise(p.get('url','')) for p in papers if p.get('url')}; seen_titles={normalise(p.get('title','')) for p in papers if p.get('title')}
    lookback_days=90 if not papers else 10; since=(datetime.now(timezone.utc)-timedelta(days=lookback_days)).date().isoformat(); candidates=[]
    for query in QUERIES:
        url='https://api.openalex.org/works?'+urlencode({'search':query,'filter':f'from_publication_date:{since},has_abstract:true','per-page':25,'sort':'publication_date:desc','select':'id,doi,title,publication_year,publication_date,authorships,primary_location,abstract_inverted_index'})
        try:
            candidates.extend(get_json(url).get('results',[]))
        except (HTTPError, URLError) as error:
            # A single temporarily unavailable query should not prevent the
            # tracker from publishing the results of its other searches.
            print(f'Skipping OpenAlex query after retries: {query!r} ({error}).', flush=True)
    # A paper may appear in more than one query; screen each OpenAlex record once.
    candidates=list({work['id']:work for work in candidates if work.get('id')}.values())
    # Restrict collection before calling either model to avoid spending tokens on
    # papers that cannot appear in the tracker.
    candidates=[work for work in candidates if allowed_journal(source_name(work))]
    candidates.sort(key=lambda work:work.get('publication_date') or '',reverse=True)
    added=0
    for work in candidates:
        if added >= MAX_NEW_PAPERS: break
        doi=work.get('doi') or ''; title_key=normalise(work.get('title',''))
        if work['id'] in seen_ids or normalise(doi) in seen_dois or title_key in seen_titles or not work.get('title'): continue
        abs_text=abstract(work)
        if not abs_text: continue
        prompt=f"Title: {work['title']}\nAbstract: {abs_text}"
        try:
            prefilter=json.loads(re.search(r'\{.*\}',text_response('gpt-5-nano',PREFILTER_SYSTEM,prompt),re.S).group())
            if not prefilter.get('candidate'): continue
            verdict=json.loads(re.search(r'\{.*\}',text_response('gpt-5.6-luna',FINAL_SYSTEM,prompt),re.S).group())
        except Exception as error: print(f"Skipping {work['id']}: {error}"); continue
        if not verdict.get('include'): continue
        source=source_name(work)
        existing['papers'].append({'id':work['id'],'title':work['title'],'authors':authors(work),'journal':source,'year':work.get('publication_year','Year unavailable'),'field':verdict['field'],'url':doi or work['id'],'summary':{k:verdict[k] for k in ('goal','methodology','finding')}}); seen_ids.add(work['id']); seen_dois.add(normalise(doi)); seen_titles.add(title_key); added+=1
    existing['papers'].sort(key=lambda p:(str(p['year']),p['title']),reverse=True); existing['updatedAt']=datetime.now(timezone.utc).isoformat(); DATA.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
