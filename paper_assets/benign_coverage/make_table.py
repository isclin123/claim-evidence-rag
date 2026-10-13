"""Table 3: corpus metadata and coverage recomputed from the frozen inputs."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json, sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'code/common.py').is_file())
sys.path.insert(0,str(ROOT/'code'))
from common import inputs, DATASETS
from official_scorer import clean_str

data=list(inputs().values())
meta=json.loads((ROOT/'data/datasets.json').read_text(encoding='utf-8'))
def fmt(x):return str(Decimal(str(x)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
lines=[]
for dataset in DATASETS+['all']:
    rows=[r for r in data if dataset=='all' or r['dataset']==dataset]
    means=[sum(sum(clean_str(r['correct_answer']) in clean_str(d) for d in r[field]) for r in rows)/len(rows)
           for field in ['benign_natural','benign_answer_bearing']]
    fields=(['Average','--','--'] if dataset=='all' else
            [meta[dataset]['paper_name'],format(meta[dataset]['corpus_documents'],','),str(len(rows))])
    lines.append(' & '.join(fields+[fmt(v) for v in means])+r' \\')
text=r'''\begin{table}[t]
\centering
\caption{Dataset statistics and benign context coverage. The coverage values denote the average number of benign supporting documents for the correct answer.}
\label{tab:benign_coverage}
\small
\begin{tabular}{lrrrr}
\toprule
Dataset & \#Docs & \#Q & Irrelevant Coverage & Answer-bearing Coverage \\
\midrule
'''+ '\n'.join(lines)+r'''
\bottomrule
\end{tabular}
\end{table}
'''
(HERE/'table_benign_coverage.tex').write_text(text,encoding='utf-8')
print('Table 3 rebuilt from 300 frozen inputs and recorded corpus metadata.')
