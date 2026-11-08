from orgchart import parse, gen_company, infer
def test_parse():
    assert parse('Support Engineer')[0] == 'Sup' and parse('DevOps Engineer')[0] == 'Eng'
    assert parse('Dir. Security') == ('Sec', 3) and parse('Head of Analytics') == ('Data', 2)
    assert parse('Sr. Data Analyst') == ('Data', 5) and parse('Chief Information Security Officer') == ('Sec', 1)
    assert parse('') == (None, None)
def test_infer_uses_only_observables():
    c = gen_company(0); obs = [{k: p[k] for k in ('t', 'loc', 'team', 'dept', 'sd')} for p in c['P']]
    assert len(infer(obs)) == len(obs)  # runs with no f/l/m/name/email at all
if __name__ == '__main__': test_parse(); test_infer_uses_only_observables(); print('tests ok')
