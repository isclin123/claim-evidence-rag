"""Score newly generated local reruns, explicitly reporting incomplete matrices."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
from official_scorer import official_attack_success

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=ROOT/'output/reruns');args=ap.parse_args()
    data=inputs();result={}
    for batch in BATCHES:
        seen=set();groups=defaultdict(list)
        for path in sorted((args.root/batch).glob('*/responses.jsonl')):
            for line in path.open(encoding='utf-8'):
                r=json.loads(line);key=tuple(r[k] for k in ['model_code','query_id','condition_id','seed'])
                assert key not in seen,key
                assert r['model_code'] in MODELS and r['condition_id'] in cells(batch) and r['seed'] in SEEDS
                assert r['dataset']==data[r['query_id']]['dataset']
                seen.add(key);hit=official_attack_success(data[r['query_id']]['target_answer'],r['response'])
                groups[(r['model_code'],r['dataset'],r['condition_id'])].append(hit)
        if not seen:continue
        result[batch]={'complete':len(seen)==EXPECTED[batch],'completed_responses':len(seen),'expected_responses':EXPECTED[batch],
                       'cells':[{'model':m,'dataset':d,'condition':c,'n':len(h),'hits':sum(h),'asr_pp':100*sum(h)/len(h)} for (m,d,c),h in sorted(groups.items())]}
    if not result:raise SystemExit('No new response files found. Dry-run files contain no responses.')
    write_json(args.root/'asr.json',result)
    print('Wrote',args.root/'asr.json','; partial runs are explicitly labeled incomplete.')
if __name__=='__main__':main()
