"""Org-chart inference: synthetic data with hidden ground truth -> rule+prior inference with abstention -> eval -> static app."""
import random, re, json, math, collections
R = random.Random(7)
# ---------- 1. GENERATOR (ground truth = true manager per person) ----------
FN = {  # key: (name aliases, IC titles, chief short, chief long)
 'Eng': (['Engineering', 'Eng.', 'Technology'], ['Software Engineer', 'Backend Developer', 'DevOps Engineer', 'QA Engineer', 'Frontend Developer'], 'CTO', 'Chief Technology Officer'),
 'Data': (['Data', 'Analytics', 'Data Science'], ['Data Analyst', 'Data Scientist', 'BI Analyst', 'Data Engineer', 'ML Engineer'], 'CDO', 'Chief Data Officer'),
 'Sec': (['Security', 'InfoSec', 'Cybersecurity'], ['Security Engineer', 'SOC Analyst', 'Security Analyst', 'GRC Specialist'], 'CISO', 'Chief Information Security Officer'),
 'Sales': (['Sales', 'Revenue', 'Business Development'], ['Account Executive', 'SDR', 'Sales Representative', 'BDR', 'Solutions Consultant'], 'CRO', 'Chief Revenue Officer'),
 'Mkt': (['Marketing', 'Growth', 'Brand'], ['Content Marketer', 'SEO Specialist', 'Marketing Associate', 'Growth Analyst'], 'CMO', 'Chief Marketing Officer'),
 'Prod': (['Product', 'Product Management'], ['Product Owner', 'UX Researcher', 'Product Analyst', 'Product Designer'], 'CPO', 'Chief Product Officer'),
 'Fin': (['Finance', 'Accounting', 'FP&A'], ['Accountant', 'Financial Analyst', 'AP Specialist'], 'CFO', 'Chief Financial Officer'),
 'HR': (['People', 'HR', 'Human Resources'], ['Recruiter', 'HR Generalist', 'Talent Partner', 'HRBP'], 'CHRO', 'Chief People Officer'),
 'Ops': (['Operations', 'Ops', 'Supply Chain'], ['Operations Analyst', 'Logistics Coordinator', 'Procurement Specialist', 'Ops Associate'], 'COO', 'Chief Operating Officer'),
 'Sup': (['Customer Support', 'Customer Success', 'Support'], ['Support Specialist', 'Customer Success Rep', 'Support Engineer', 'CS Associate'], None, None)}
CITIES = ['Sydney', 'Melbourne', 'London', 'New York', 'Austin', 'Singapore', 'Berlin', 'Toronto', 'Mumbai']
INDS = ['SaaS', 'Fintech', 'Healthcare', 'Retail', 'Manufacturing', 'Logistics', 'Media', 'Energy', 'Education']
NA = ['Apex', 'Blue', 'Nova', 'Quantum', 'Iron', 'Bright', 'Delta', 'Lumen', 'Orbit', 'Vertex', 'Cedar', 'Summit']
NB = ['Systems', 'Labs', 'Group', 'Works', 'Partners', 'Dynamics', 'Networks', 'Holdings', 'Health', 'Logic']

def title(f, l):
    al = R.choice(FN[f][0])
    if l == 1: t = R.choice([FN[f][2], FN[f][3]])
    elif l == 2: t = R.choice([f"VP {al}", f"Vice President, {al}", f"Head of {al}", f"VP of {al}"])
    elif l == 3: t = R.choice([f"Director of {al}", f"{al} Director", f"Dir. {al}", f"Director, {al}"])
    elif l == 4: t = R.choice([f"{al} Manager", f"Manager, {al}", f"{al} Mgr", f"{al} Team Lead"])
    else: t = R.choice(['', '', 'Senior ', 'Sr. ', 'Junior ', 'Staff ']) + R.choice(FN[f][1])
    if R.random() < .04 and len(t) > 4:  # typo
        i = R.randrange(len(t) - 2); t = t[:i] + t[i + 1] + t[i] + t[i + 2:]
    return '' if R.random() < .03 else t  # missing title

def gen_company(ci):
    n = R.choice([100, 110, 120, 140, 160, 200, 250])
    cities = R.sample(CITIES, R.randint(1, 5)); P = []
    def add(f, l, m, loc, team=None):
        P.append(dict(f=f, l=l, m=m, loc=loc, team=team)); return len(P) - 1
    pick = lambda xs: R.choice(xs)
    ceo = add(None, 0, None, cities[0]); P[0]['t'] = R.choice(['CEO', 'Chief Executive Officer', 'Founder & CEO'])
    funcs = ['Eng', 'Ops'] + R.sample([k for k in FN if k not in ('Eng', 'Ops')], R.randint(4, 8))
    w = {f: R.random() + .3 for f in funcs}; tot = sum(w.values()); chief = {}
    for f in funcs:
        h = max(5, math.ceil((n - 1) * w[f] / tot)); L = lambda p: pick(cities) if R.random() > .8 else P[p]['loc']
        if FN[f][2] and not (f in ('Data', 'Sec') and R.random() < .5):
            head = add(f, 1, ceo, cities[0]); chief[f] = head; vps = [head]
            if h >= 25: vps += [add(f, 2, head, pick(cities)) for _ in range(h // 30 + 1)]
        else:
            par = ceo; r = R.random()
            if f in ('Data', 'Sec') and 'Eng' in chief: par = chief['Eng'] if r < .6 else (ceo if r < .85 else chief.get('Ops', ceo))
            if f == 'Sup' and 'Ops' in chief: par = chief['Ops'] if r < .7 else ceo
            head = add(f, 2, par, pick(cities)); vps = [head]
        dirs = [add(f, 3, pick(vps), pick(cities)) for _ in range(h // 14)] or vps
        mgrs = []
        for k in range(h // 6):
            d = pick(dirs); mgrs.append(add(f, 4, d, L(d), f"{f}-{k}"))
        used = len(P) - sum(1 for p in P if p['f'] != f)  # people in f so far
        for _ in range(h - used):
            par = pick(mgrs) if mgrs and R.random() > .08 else pick(dirs)
            i = add(f, 5, par, L(par), P[par]['team'] if P[par]['l'] == 4 and R.random() < .65 else None)
    for p in P:  # render messy fields
        p['t'] = p.get('t') or title(p['f'], p['l'])
        if R.random() < .03: p['loc'] = None
    return dict(name=f"{pick(NA)} {pick(NB)} {ci}", ind=pick(INDS), P=P)

# ---------- 2. INFERENCE (no access to f/l/m truth fields) ----------
PAT = [('Sec', r'secur|infosec|ciso|\bsoc\b|\bgrc\b'), ('Data', r'\bdata\b|analytics|\bbi\b|\bml\b|\bcdo\b'),
 ('Sup', r'support|customer|\bcs\b'), ('Sales', r'sales|revenue|account exec|\bsdr\b|\bbdr\b|business dev|solutions|\bcro\b'),
 ('Prod', r'product|\bux\b|\bcpo\b'), ('Mkt', r'market|growth|brand|content|\bseo\b|\bcmo\b'),
 ('Fin', r'financ|account|fp&a|\bap\b|\bcfo\b'), ('HR', r'people|\bhr\b|hrbp|human|recruit|talent|chro'),
 ('Ops', r'operations|\bops\b|logistic|procure|supply|\bcoo\b'), ('Eng', r'engineer|software|developer|devops|\bqa\b|technology|\beng\b|\bcto\b')]
def parse(t):
    s = t.lower()
    if not s: return None, None
    if re.search(r'chief executive|\bceo\b|founder', s): return None, 0
    f = next((k for k, p in PAT if re.search(p, s)), None)
    if re.search(r'chief|\b(cto|cdo|ciso|cmo|cpo|cfo|chro|coo|cro)\b', s): l = 1
    elif re.search(r'\bvp\b|vice president|head of', s): l = 2
    elif re.search(r'director|\bdir\b', s): l = 3
    elif re.search(r'manager|mgr|team lead', s): l = 4
    else: l = 5
    return f, l
PRIOR = {'Data': ('Eng', .6), 'Sec': ('Eng', .6), 'Sup': ('Ops', .7)}  # cross-function heads: weak priors

def infer(P):
    pr = [parse(p['t']) for p in P]; idx = collections.defaultdict(list)
    for i, (f, l) in enumerate(pr):
        if l is not None: idx[(f, l)].append(i)
    ceos = idx[(None, 0)]; out = []
    for i, p in enumerate(P):
        f, l = pr[i]
        if l is None or l == 0 or (f is None): out.append((-1, 0)); continue
        if l == 1:
            out.append((ceos[0], .99) if len(ceos) == 1 else (-1, 0)); continue
        c = next((idx[(f, k)] for k in range(l - 1, 0, -1) if idx[(f, k)]), [])
        if not c:  # no manager level in own function: use priors, else CEO as a low-confidence fallback
            g, pc = PRIOR.get(f, (None, 0)); cg = idx[(g, 1)] if g else []
            out.append((cg[0], pc) if len(cg) == 1 else ((ceos[0], .3) if len(ceos) == 1 else (-1, 0))); continue
        if len(c) == 1: out.append((c[0], .95)); continue
        m = [x for x in c if p['team'] and P[x]['team'] == p['team']]
        if len(m) == 1: out.append((m[0], .92)); continue
        lc = [x for x in c if p['loc'] and P[x]['loc'] == p['loc']]
        pool, fac = (lc, .85) if lc else (c, .6)
        out.append((pool[0], round(fac / len(pool), 2)))
    return out

# ---------- 3. EVAL ----------
def evaluate(cos):
    rows = [(p['l'], pred, conf, pred == p['m']) for c in cos for p, (pred, conf) in zip(c['P'], c['I']) if p['l'] > 0]
    res = {}
    for th in (0, .5, .7, .9):
        e = [r for r in rows if r[1] >= 0 and r[2] >= th]
        res[th] = dict(emitted=len(e), coverage=round(len(e) / len(rows), 3), precision=round(sum(r[3] for r in e) / max(1, len(e)), 3))
    cal = {}
    for lo in (0, .3, .5, .7, .9):
        b = [r for r in rows if r[1] >= 0 and lo <= r[2] < (lo + .2 if lo < .9 else 1.01)]
        cal[f"{lo}-{round(lo + .2, 1) if lo < .9 else 1.0}"] = (len(b), round(sum(r[3] for r in b) / max(1, len(b)), 3))
    lv = {l: (lambda e: (round(sum(r[3] for r in e) / max(1, len(e)), 3), round(len(e) / max(1, sum(r[0] == l for r in rows)), 3)))([r for r in rows if r[0] == l and r[1] >= 0 and r[2] >= .7]) for l in range(1, 6)}
    return dict(total_people=len(rows) + len(cos), by_threshold=res, calibration=cal, level_precision_coverage_at_70=lv)

if __name__ == '__main__':
    cos = [gen_company(i) for i in range(500)]
    for c in cos: c['I'] = infer(c['P'])
    M = evaluate(cos); print(json.dumps(M, indent=1)); json.dump(M, open('metrics.json', 'w'), indent=1)
    D = dict(c=[dict(n=c['name'], i=c['ind'], p=[[p['t'], p['loc'] or '', I[0], int(I[1] * 100), p['m'] if p['m'] is not None else -1] for p, I in zip(c['P'], c['I'])] ) for c in cos])
    html = open('template.html').read().replace('__DATA__', json.dumps(D, separators=(',', ':'))).replace('__META__', json.dumps(M))
    open('index.html', 'w').write(html); print(len(html) / 1e6, 'MB')
