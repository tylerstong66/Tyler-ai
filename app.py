import os,re,json,hmac,requests
from datetime import datetime,timedelta,timezone
from flask import Flask,request,jsonify,render_template_string,session,redirect,url_for
app=Flask(__name__)
N8N_WEBHOOK_URL=os.getenv('N8N_WEBHOOK_URL'); TYLER_API_KEY=os.getenv('TYLER_API_KEY'); GROQ_API_KEY=os.getenv('GROQ_API_KEY'); TAVILY_API_KEY=os.getenv('TAVILY_API_KEY'); TYLER_DEFAULT_EMAIL=os.getenv('TYLER_DEFAULT_EMAIL'); SUPABASE_URL=os.getenv('SUPABASE_URL'); SUPABASE_KEY=os.getenv('SUPABASE_KEY'); GROQ_MODEL=os.getenv('GROQ_MODEL','openai/gpt-oss-20b')
VERSION='2.8.1-approval-gate-fix'; VERSION_SHORT='v2.8.1'; MAX_STEPS=8; SPECIAL={'task_state','decision_log','feedback'}
app.secret_key=os.getenv('FLASK_SECRET_KEY') or TYLER_API_KEY or os.urandom(32); app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=True,PERMANENT_SESSION_LIFETIME=timedelta(days=7))
def norm(v): return re.sub(r'\s+',' ',str(v or '')).strip()
def low(v): return norm(v).lower().replace('tlyer','tyler').replace('tyelr','tyler')
def now(): return datetime.now(timezone.utc).isoformat()
def auth():
    k=request.headers.get('X-Tyler-Key'); return bool(TYLER_API_KEY and k and hmac.compare_digest(k,TYLER_API_KEY))
def groq(msg,tokens=800,json_mode=False):
    if not GROQ_API_KEY: raise RuntimeError('GROQ_API_KEY is not configured')
    p={'model':GROQ_MODEL,'messages':msg,'temperature':0 if json_mode else .2,'max_completion_tokens':tokens,'reasoning_effort':'low','include_reasoning':False}
    if json_mode:p['response_format']={'type':'json_object'}
    r=requests.post('https://api.groq.com/openai/v1/chat/completions',headers={'Authorization':f'Bearer {GROQ_API_KEY}','Content-Type':'application/json'},json=p,timeout=90); d=r.json()
    if not r.ok: raise RuntimeError((d.get('error') or {}).get('message',str(d)))
    return str(((d.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
def js(text):
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',str(text or '').strip(),flags=re.I)
    try:return json.loads(text)
    except Exception:
        a,b=text.find('{'),text.rfind('}')
        try:return json.loads(text[a:b+1]) if a>=0 and b>a else None
        except Exception:return None
def sh(): return {'apikey':SUPABASE_KEY,'Authorization':f'Bearer {SUPABASE_KEY}','Content-Type':'application/json'}
def memories(limit=100,cat=None):
    if not SUPABASE_URL:return []
    p={'select':'id,created_at,memories,category,importance','order':'created_at.desc','limit':limit};
    if cat:p['category']=f'eq.{cat}'
    r=requests.get(f'{SUPABASE_URL}/rest/v1/memories',headers=sh(),params=p,timeout=30)
    if not r.ok:raise RuntimeError('Supabase read failed')
    return r.json()
def one(i): return next((x for x in memories(300) if int(x.get('id',-1))==int(i)),None)
def save(text,cat='general',importance=5):
    r=requests.post(f'{SUPABASE_URL}/rest/v1/memories',headers={**sh(),'Prefer':'return=representation'},json={'memories':text,'category':cat,'importance':importance},timeout=30)
    if not r.ok:raise RuntimeError('Supabase save failed')
    return r.json()
def patch(i,text,cat='task_state',importance=1):
    r=requests.patch(f'{SUPABASE_URL}/rest/v1/memories',headers={**sh(),'Prefer':'return=representation'},params={'id':f'eq.{int(i)}'},json={'memories':text,'category':cat,'importance':importance},timeout=30)
    if not r.ok:raise RuntimeError('Supabase update failed')
def normal(limit=20): return [x for x in memories(max(60,limit*4)) if str(x.get('category','')).lower() not in SPECIAL][:limit]
def core(): return f"Tyler AI personal autonomous assistant. Flask/Render, Groq reasoning/planning, Supabase memory/tasks/journal/feedback, Tavily research, n8n email. Multi-step tasks, approval gates, validation, retry/replanning and resumable state are active. Version {VERSION}."
def pctx(): return 'CANONICAL PROJECT PROFILE:\n'+core()+'\n'+ '\n'.join(f"- [{x.get('category')}] {norm(x.get('memories'))[:300]}" for x in normal(12))
def project(m): return 'tyler ai' in low(m) or 'tyler project' in low(m)
def needmem(m): return project(m) or any(x in low(m) for x in ['what do you remember','using what you remember','based on what you know','my goals','my preferences'])
def research(m): return any(x in low(m) for x in ['research','latest','current','today','recent','news','look up','search'])
def memdeny(m): return any(x in low(m) for x in ['do not save',"don't save",'dont save','do not remember',"don't remember",'no memory','do not store'])
def memintent(m):
    t=low(m)
    if memdeny(m):return False
    return any(x in t for x in ['remember that','remember this','save to memory','save this','save that','store this','create a memory','create memory','add to memory','put this in memory','before saving','before you save']) or ('memory' in t and any(x in t for x in ['save','saving','store','remember','record','create']))
def emaildeny(m): return any(x in low(m) for x in ['do not email',"don't email",'dont email','no email'])
def emailintent(m): return not emaildeny(m) and any(x in low(m) for x in ['email me','send me an email','email the result','send the result to my email'])
def gate(m): return any(x in low(m) for x in ['after i approve','once i approve','wait for my approval','ask me before','ask for approval','ask for my approval','before saving','before you save','before emailing','before you email'])
def taskmode(m): return any(x in low(m) for x in ['plan and execute','complete this task','multi-step','multistep','break this into steps','create a plan and execute']) or sum([needmem(m),research(m),memintent(m),emailintent(m)])>=3
def requested_memory(m):
    q=re.search(r'(?is)create\s+(?:a\s+)?(?:short\s+)?memory\s+(?:entry\s+)?saying\s+that\s+(.+?)(?=\.?(?:\s+ask\b|\s+before\b|\s+do not\b|\s+don\'t\b|$))',norm(m))
    if not q:return ''
    v=q.group(1).strip().rstrip(' .'); return (v[0].upper()+v[1:]+'.')[:500] if v else ''
def web(q):
    r=requests.post('https://api.tavily.com/search',headers={'Authorization':f'Bearer {TAVILY_API_KEY}','Content-Type':'application/json'},json={'query':q,'search_depth':'basic','include_answer':True,'max_results':4},timeout=60); d=r.json()
    if not r.ok:raise RuntimeError('Tavily failed')
    return {'answer':norm(d.get('answer'))[:1200],'sources':[{'title':x.get('title',''),'url':x.get('url',''),'content':norm(x.get('content'))[:350]} for x in d.get('results',[])[:4]]}
def mail(body):
    r=requests.post(N8N_WEBHOOK_URL,json={'action':'email','data':{'to':TYLER_DEFAULT_EMAIL,'subject':'Tyler AI Task Results','message':body}},timeout=60)
    if not r.ok:raise RuntimeError('Email failed')
def step(i,tool,desc,approval=False): return {'id':i,'tool':tool,'description':desc,'status':'pending','attempts':0,'requires_approval':approval,'approved':False,'error':''}
def effects(m): return (['save_memory'] if memintent(m) else [])+(['send_email'] if emailintent(m) else [])
def plan(m):
    allowed=['read_memory','research_web','reason']+effects(m); prompt=f'''Plan this task with at most {MAX_STEPS} steps. Goal: {m}\nAllowed tools: {allowed}. Put gathering before reason and side effects last. Return JSON {{"goal":"...","steps":[{{"tool":"reason","description":"..."}}]}}'''
    try:p=js(groq([{'role':'user','content':prompt}],550,True)) or {}; raw=p.get('steps') or []; goal=norm(p.get('goal') or m)[:500]
    except Exception:raw=[];goal=norm(m)[:500]
    out=[];seen=set()
    def add(tool,desc):
        if tool in seen:return
        seen.add(tool); out.append(step(len(out)+1,tool,desc,tool in {'save_memory','send_email'} and gate(m)))
    if needmem(m):add('read_memory','Read relevant saved context.')
    if research(m):add('research_web','Research current information.')
    for x in raw:
        if isinstance(x,dict) and x.get('tool') in allowed and x.get('tool') not in {'save_memory','send_email'}:add(x['tool'],norm(x.get('description') or x['tool'])[:260])
    add('reason','Synthesize the gathered information and produce the result.')
    for e in effects(m):add(e,'Save the requested result to long-term memory.' if e=='save_memory' else 'Email the completed result to the user.')
    return goal,out[:MAX_STEPS]
def persist(t):
    i=t['task_id']; d=dict(t); d.pop('task_id',None); d['updated_at']=now(); patch(i,json.dumps(d,separators=(',',':'),ensure_ascii=False))
def create(m):
    goal,steps=plan(m); t={'version':VERSION,'goal':goal,'original_request':norm(m),'status':'running','created_at':now(),'current_step':0,'steps':steps,'context':[],'sources':[],'final_answer':'','requested_memory':requested_memory(m),'required_effects':effects(m),'replans':0,'last_error':''}; r=save(json.dumps(t,separators=(',',':')),'task_state',1); t['task_id']=int(r[0]['id']);persist(t);return t
def load(i):
    r=one(i)
    if not r or r.get('category')!='task_state':raise RuntimeError('Task not found')
    t=json.loads(r['memories']);t['task_id']=int(r['id']);return t
def progress(t): return sum(s.get('status')=='completed' for s in t['steps']),len(t['steps'])
def execstep(t,s):
    if s['tool']=='read_memory':r=pctx();t['context'].append(r);return r
    if s['tool']=='research_web':d=web(t['original_request']);r=d['answer']+'\n'+'\n'.join(x['content'] for x in d['sources']);t['context'].append(r);t['sources']=d['sources'];return r
    if s['tool']=='reason':
        prompt=f"Goal: {t['original_request']}\nContext:\n"+'\n\n'.join(t['context'][-8:])+"\nProduce the final answer. Do not claim save/email happened yet. End with RECOMMENDATION: <sentence> or RECOMMENDATION: None";r=groq([{'role':'system','content':'You are Tyler AI.'},{'role':'user','content':prompt}],1000);t['final_answer']=r;return r
    if s['tool']=='save_memory':
        c=t.get('requested_memory') or ('Tyler AI task result: '+norm(t.get('final_answer'))[:450]);
        if not c:raise RuntimeError('Nothing to save')
        if not any(norm(x.get('memories')).lower()==c.lower() for x in normal(100)):save(c,'task_result',7)
        return c
    if s['tool']=='send_email':
        if not t.get('final_answer'):raise RuntimeError('Nothing to email')
        mail(t['final_answer']);return 'sent'
def replan(t,failed):
    if t['replans']>=2:return False
    t['replans']+=1
    if failed['tool']=='research_web':
        prefix=t['steps'][:t['current_step']]; prefix.append(step(max([x['id'] for x in t['steps']])+1,'reason','Continue from available context.'));t['steps']=prefix;t['status']='running';return True
    return False
def run(i,approved=None,planner_call=0):
    t=load(i);used=[];calls=planner_call
    if t['status']=='awaiting_approval' and approved is None:return payload(t,used,calls)
    if t['status'] in {'completed','failed','cancelled'}:return payload(t,used,calls)
    t['status']='running'
    while True:
        idx=t['current_step']
        if idx>=len(t['steps']):
            done={x['tool'] for x in t['steps'] if x['status']=='completed'}; miss=[x for x in t['required_effects'] if x not in done]
            if miss:t['status']='failed';t['last_error']='Missing requested action: '+','.join(miss)
            else:t['status']='completed'
            persist(t);break
        s=t['steps'][idx]
        if s['status']=='completed':t['current_step']+=1;persist(t);continue
        if s['requires_approval'] and not s['approved']:
            if approved==s['id']:s['approved']=True;approved=None
            else:s['status']='awaiting_approval';t['status']='awaiting_approval';persist(t);break
        s['status']='running';s['attempts']+=1;persist(t)
        try:execstep(t,s);calls+=1 if s['tool']=='reason' else 0;s['status']='completed';s['error']='';t['current_step']+=1;used.append(s['tool']);persist(t)
        except Exception as e:
            s['error']=str(e);t['last_error']=str(e)
            if s['attempts']<2:s['status']='pending';persist(t);continue
            s['status']='failed';persist(t)
            if replan(t,s):persist(t);continue
            t['status']='failed';persist(t);break
    return payload(load(i),used,calls)
def payload(t,used,calls):
    d,n=progress(t);idx=t['current_step'];cur=t['steps'][idx] if idx<n else None
    if t['status']=='completed':reply=(t.get('final_answer') or 'Task completed.')+f'\n\nTask {t["task_id"]} completed ({d}/{n} steps).'
    elif t['status']=='awaiting_approval':reply=f'Task {t["task_id"]} is paused for approval.\n\nNext step: {cur["description"]}\nTool: {cur["tool"]}\n\nTo approve only this step, send exactly:\nApprove task {t["task_id"]}\n\nProgress: {d}/{n} steps complete.'
    else:reply=f'Task {t["task_id"]} is {t["status"]}. {d}/{n} steps. '+t.get('last_error','')
    return {'success':True,'type':'multi_step_task','version':VERSION,'reply':reply,'used_tools':used,'controller_attempts':0,'controller_successes':0,'priority_decisions':0,'fallback_decisions':0,'reasoning_calls':0,'total_groq_calls':calls,'memory_result':None,'email_result':None,'sources':t.get('sources',[]),'task_result':{'task_id':t['task_id'],'status':t['status'],'completed_steps':d,'total_steps':n,'current_tool':cur['tool'] if cur else None,'replan_count':t['replans']}}
def taskid(m):
    q=re.search(r'(?i)task\s+#?(\d+)',m);return int(q.group(1)) if q else None
def journal(m,p):
    try:r=save(json.dumps({'request':norm(m)[:600],'type':p.get('type'),'tools':p.get('used_tools'),'task_id':(p.get('task_result') or {}).get('task_id'),'success':True},separators=(',',':')),'decision_log',1);return {'logged':True,'id':r[0]['id']}
    except Exception as e:return {'logged':False,'error':str(e)[:100]}
def simple(m):
    ctx=pctx() if needmem(m) else '';live='';src=[]
    if research(m):
        try:d=web(m);live=d['answer']+'\n'+'\n'.join(x['content'] for x in d['sources']);src=d['sources']
        except Exception as e:live='Research failed: '+str(e)
    r=groq([{'role':'system','content':'You are Tyler AI.'},{'role':'user','content':f'User: {m}\nSaved context: {ctx or "None"}\nLive research: {live or "None"}\nAnswer clearly. End with RECOMMENDATION: <sentence> or RECOMMENDATION: None'}],900)
    return {'success':True,'type':'autonomous_agent','version':VERSION,'reply':r,'used_tools':(['read_memory'] if ctx else [])+(['research_web'] if live else [])+['reason'],'controller_attempts':0,'controller_successes':0,'priority_decisions':0,'fallback_decisions':0,'reasoning_calls':1,'total_groq_calls':1,'memory_result':None,'email_result':None,'sources':src,'task_result':None}
def handle(m):
    if re.fullmatch(r'(?i)approve\s+task\s+#?\d+',norm(m)):
        t=load(taskid(m));s=t['steps'][t['current_step']] if t['current_step']<len(t['steps']) else None;p=run(t['task_id'],s['id'] if s else None);p['decision_log_result']=journal(m,p);return p,200
    if re.fullmatch(r'(?i)(resume|continue|run)\s+task\s+#?\d+',norm(m)):
        p=run(taskid(m));p['decision_log_result']=journal(m,p);return p,200
    if taskmode(m):
        t=create(m);p=run(t['task_id'],planner_call=1);p['decision_log_result']=journal(m,p);return p,200
    p=simple(m);p['decision_log_result']=journal(m,p);return p,200
LOGIN='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="background:#07111f;color:white;font-family:sans-serif"><form method="post" action="/ui/login" style="max-width:400px;margin:20vh auto"><h1>Tyler AI</h1>{% if error %}<p>{{error}}</p>{% endif %}<input name="key" type="password" style="width:100%;padding:14px"><button style="width:100%;padding:14px;margin-top:10px">Open Tyler AI</button></form></body>'''
CHAT='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="background:#07111f;color:white;font-family:sans-serif"><h3>Tyler AI · {{v}}</h3><div id="c">Tyler AI is online.</div><textarea id="m" style="width:80%;padding:12px"></textarea><button id="s">Send</button><script>const c=document.getElementById('c'),m=document.getElementById('m'),s=document.getElementById('s');async function go(){let t=m.value.trim();if(!t)return;c.innerHTML+='<p><b>You:</b> '+t.replaceAll('<','&lt;')+'</p>';m.value='';let r=await fetch('/ui/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t})});let d=await r.json();c.innerHTML+='<pre style="white-space:pre-wrap">'+(d.reply||d.error)+'</pre>'}s.onclick=go;m.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();go()}}</script></body>'''
@app.route('/')
@app.route('/ui')
def ui():return render_template_string(CHAT,v=VERSION_SHORT) if session.get('ok') else render_template_string(LOGIN,error=None)
@app.route('/ui/login',methods=['POST'])
def login():
    k=str(request.form.get('key',''))
    if not TYLER_API_KEY or not hmac.compare_digest(k,TYLER_API_KEY):return render_template_string(LOGIN,error='Key not accepted'),401
    session['ok']=True;session.permanent=True;return redirect(url_for('ui'))
@app.route('/ui/chat',methods=['POST'])
def uichat():
    if not session.get('ok'):return jsonify({'success':False,'error':'Unauthorized'}),401
    try:p,s=handle(str((request.get_json(silent=True) or {}).get('message','')).strip());return jsonify(p),s
    except Exception as e:return jsonify({'success':False,'error':str(e),'version':VERSION}),500
@app.route('/chat',methods=['POST'])
def chat():
    if not auth():return jsonify({'success':False,'error':'Unauthorized'}),401
    try:p,s=handle(str((request.get_json(silent=True) or {}).get('message','')).strip());return jsonify(p),s
    except Exception as e:return jsonify({'success':False,'error':str(e),'version':VERSION}),500
@app.route('/health')
def health():return jsonify({'status':'healthy','version':VERSION})
@app.route('/status')
def status():return jsonify({'name':'Tyler AI','status':'online','version':VERSION,'groq':bool(GROQ_API_KEY),'tavily':bool(TAVILY_API_KEY),'memory':bool(SUPABASE_URL and SUPABASE_KEY),'n8n':bool(N8N_WEBHOOK_URL)})
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT',10000)))
