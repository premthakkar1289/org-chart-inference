# Org chart inference

`python orgchart.py` generates 500 companies (100-250 people, 79k total), infers reporting lines, evaluates them, and writes `metrics.json` and a self-contained `index.html` (the app; `template.html` is its source).

## Data design: how we know if inference is right
The generator builds a true tree first, then renders it messily. Truth (`m`, `f`, `l`) never reaches the inference code, which sees only title, location and team.
- Structure: CEO > function chiefs > VPs > directors > managers > ICs, with skipped layers.
- Cross-function heads (Data, Security, Support) have no chief in about half the companies and report to the CTO/COO/CEO with realistic odds. This is the hard case.
- Fields per person: name, job title, location, team, department, start date, work email. Inference uses only title, location, team, department and start date (email is realistic noise, not used).
- Leak guard: `infer` receives only observable fields, and `tests.py` checks it runs without truth fields.
- Noise: title variants and abbreviations ("Sr.", "Mgr", "Dir.", "VP of"), 4% typos, 3% missing titles, 3% missing location, 35% of ICs missing team, 8% of ICs skipping a layer.

## Inference
1. Normalise each title to (function, level) with ordered regexes.
2. Candidate managers: people in the same function at the nearest populated level above.
3. Narrow candidates by team match, then location, then start date (managers usually start earlier); department is a fallback for the function when the title fails (confidence x0.8), then by weak function-head priors (for example Data head to CTO at 0.6).
4. Confidence: 0.95 for a single candidate, 0.92 for a unique team match, otherwise (0.85 if location matched, else 0.6) divided by the number of candidates left. Unparseable titles abstain.
5. The app has a confidence slider. Edges below it are shown as unresolved, so a wrong edge costs coverage instead of precision.

## Results (500 companies, 79,669 people)
| min conf | precision | coverage |
|---|---|---|
| 0 (guess everything) | 75.8% | 96.7% |
| 0.5 | 90.4% | 73.9% |
| 0.7 | 91.1% | 72.6% |
| 0.9 | 96.1% | 61.2% |

Calibration (bucket: actual precision): 0-0.2: 14%, 0.3-0.5: 35%, 0.5-0.7: 52%, 0.7-0.9: 65%, 0.9-1.0: 96%. Scores track reality, so the threshold is meaningful. Weakest: directors (about 80% precision) and Data/Security/Support heads without a chief.
Adding department and start date lifted coverage at 0.7 from 66.9% to 72.6% for a small precision cost (92.4% to 91.1%).

## Known limits and next steps
- Real data is not synthetic. The generator's noise model is my assumption, and the true test is a hand-labelled sample.
- Next: an LLM pass only for low-confidence or unparseable titles, using tenure and email-domain signals, scored by this same harness.

## Run it
```
python orgchart.py        # regenerates data, metrics.json and index.html (stdlib only, Python 3.8+)
cp index.html docs/index.html
```
Live app: <PASTE YOUR DEPLOYED LINK HERE>
