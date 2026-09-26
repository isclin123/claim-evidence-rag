"""Offline integrity, method reconstruction, matrix and exact-prompt verification."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import sys
import subprocess
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
from constructions import construct
from official_scorer import self_test

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--skip-manifest',action='store_true');a=ap.parse_args()
    if not a.skip_manifest:
        manifest=read_json(ROOT/'provenance/files.json')
        expected=set(manifest['files'])
        actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and not any(x in ['output','__pycache__','.git','.venv'] for x in p.relative_to(ROOT).parts)}-{'provenance/files.json'}
        assert actual==expected,{'missing':sorted(expected-actual),'unexpected':sorted(actual-expected)}
        for name,h in manifest['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    assert self_test()['passed']
    data=inputs();protocol=read_json(ROOT/'data/protocol.json')
    assert set(METHODS)=={'C00','C06','C42'}
    assert len(MODELS)==8 and set(read_json(ROOT/'data/models.json'))==set(MODELS)
    assert set(read_json(ROOT/'results/statistical_families.json'))=={
        'D4-method','E1-position','E1-baseline-position','E3-front-tail'}
    with (ROOT/'paper_assets/method_ci/data/contrasts.csv').open(encoding='utf-8',newline='') as f:
        contrasts=list(csv.DictReader(f))
    assert len(contrasts)==4 and all(int(r['models'])==8 for r in contrasts)
    assert {r['family'] for r in contrasts}=={'D4-method','posthoc-closest-by-position'}
    assert collections.Counter(r['dataset'] for r in data.values())==dict.fromkeys(DATASETS,100)
    checked=0
    for row in data.values():
        assert set(row['documents'])==set(METHODS)
        assert len(row['benign_natural'])==len(row['benign_answer_bearing'])==4
        for method,docs in row['documents'].items():
            assert len(docs)==(1 if method=='C42' else 5)
            for j,doc in enumerate(docs):
                assert construct(row['question'],row['correct_answer'],row['target_answer'],row['base_passages'][j],method)==doc,(row['query_id'],method,j)
                checked+=1
    report={'reconstructed_documents':checked,'inputs':len(data),'methods':METHODS,
            'local_models':len(MODELS),'batches':{}}
    schedule_rows=list(read_rows(ROOT/'data/schedules.jsonl.gz'))
    schedules={(r['batch'],r['model']):r['schedule'] for r in schedule_rows}
    assert len(schedule_rows)==len(schedules)==len(BATCHES)*len(MODELS)
    assert set(schedules)=={(b,m) for b in BATCHES for m in MODELS}
    for batch in BATCHES:
        seen=set();cached={};ordered=collections.defaultdict(list)
        for r in responses(batch):
            q=data[r['query_id']];key=(r['model_code'],r['query_id'],r['condition_id'],r['seed'])
            assert key not in seen and r['seed'] in SEEDS and r['model_code'] in MODELS,key
            assert r['condition_id'] in cells(batch) and r['dataset']==q['dataset']
            seen.add(key);pk=(r['query_id'],r['condition_id'])
            if pk not in cached:cached[pk]=sha_text(prompt(q,batch,r['condition_id'],protocol))
            assert cached[pk]==r['prompt_sha256'],(batch,pk,'prompt')
            assert sha_text(r['response'])==r['response_sha256']
            options=request(q,batch,r['condition_id'],r['seed'],'unused',protocol)['options']
            assert sha_text(json.dumps(options,ensure_ascii=False,sort_keys=True,separators=(',',':')))==r['request_options_sha256']
            assert sha_text(protocol['system_prompt'])==r['system_prompt_sha256']
            ordered[r['model_code']].append(list(key[1:]))
        assert len(seen)==EXPECTED[batch],(batch,len(seen))
        for model,seq in ordered.items():assert seq==schedules[(batch,model)]
        report['batches'][batch]=len(seen);print(batch,len(seen),'exact prompts and complete matrix OK',flush=True)
    cr=list(responses('commercial'));prompt_rows=list(read_rows(ROOT/'data/commercial_prompts.jsonl.gz'))
    cp={(r['sample_id'],r['method'],r['k']):r for r in prompt_rows}
    assert len(cr)==1800 and len(cp)==600
    assert len(prompt_rows)==600
    assert {r['method'] for r in cr}=={r['method'] for r in prompt_rows}=={'original','claim_evidence'}
    assert {r['k'] for r in cr}=={r['k'] for r in prompt_rows}==set(range(1,6))
    assert len({r['trial_id'] for r in cr})==1800
    valid=0
    for r in cr:
        p=cp[(r['sample_id'],r['method'],r['k'])]
        assert sha_text(p['prompt'])==r['prompt_sha256']==p['prompt_sha256']
        if r['status']=='completed':
            assert sha_text(r['final_answer'])==r['answer_sha256'];valid+=1
        else:assert r['final_answer'] is None and r['finish_reason'].startswith('platform_safety_block')
    assert valid==1798
    sample=read_json(ROOT/'data/commercial_sample.json')['rows']
    assert len(sample)==60 and len({r['sample_id'] for r in sample})==60
    for ds in DATASETS:
        ranked=sorted((sha_text(f'BB60-v1|20260912|{ds}|{q}'),q)
                      for q,v in data.items() if v['dataset']==ds)[:20]
        chosen=sorted((r['sampling_hash'],r['query_id']) for r in sample if r['dataset']==ds)
        assert chosen==ranked,('commercial subset',ds)
    keys={(r['model_id'],r['sample_id'],r['method'],r['k']) for r in cr}
    assert keys=={(m,r['sample_id'],method,k) for m in ['M01','M02','M03']
                  for r in sample for method in ['original','claim_evidence'] for k in range(1,6)}
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/verify_paper_outputs.py'),'--inventory-only'],check=True)
    report.update(commercial_valid=valid,commercial_blocked=2,passed=True)
    write_json(ROOT/'output/verification.json',report)
    print('PASS',json.dumps(report))
if __name__=='__main__':main()
