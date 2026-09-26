"""Rerun one selected manuscript batch/model on local Ollama; dry run by default."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request
import urllib.parse
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--batch',choices=BATCHES,required=True);ap.add_argument('--model',choices=MODELS,required=True)
    ap.add_argument('--limit',type=int);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--endpoint',default='http://127.0.0.1:11434')
    ap.add_argument('--allow-model-drift',action='store_true',help='Use a different model digest; output records the actual digest.')
    args=ap.parse_args()
    if args.limit is not None and args.limit<1:ap.error('--limit must be positive')
    u=urllib.parse.urlparse(args.endpoint)
    if u.scheme!='http' or u.hostname not in ['127.0.0.1','localhost','::1']:ap.error('This runner accepts a local Ollama endpoint only')
    data=inputs();proto=read_json(ROOT/'data/protocol.json');model=read_json(ROOT/'data/models.json')[args.model]
    schedule=next(r['schedule'] for r in read_rows(ROOT/'data/schedules.jsonl.gz') if r['batch']==args.batch and r['model']==args.model)
    selected=schedule[:args.limit] if args.limit else schedule
    out=ROOT/'output/reruns'/args.batch/args.model;out.mkdir(parents=True,exist_ok=True)
    jobs=[request(data[q],args.batch,c,s,model['tag'],proto) for q,c,s in selected]
    if not args.execute:
        write_json(out/'dry_run.json',{'requests':len(jobs),'model':model,'first_key':selected[0],'first_request':jobs[0],'network_calls':0})
        print(f'Dry run: {len(jobs)} requests; zero model calls. Add --execute to run.');return
    with urllib.request.urlopen(args.endpoint+'/api/tags',timeout=30) as f:tags=json.load(f)['models']
    match=next((t for t in tags if t['name']==model['tag']),None)
    if match is None:raise RuntimeError('Install the exact documented model before running: '+model['tag'])
    if match['digest']!=model['digest'] and not args.allow_model_drift:raise RuntimeError('Model digest differs from the recorded run; see ENVIRONMENT.md')
    run_protocol={'batch':args.batch,'model_code':args.model,'model_tag':model['tag'],'actual_digest':match['digest'],'protocol':proto}
    # Exclusive lock prevents two processes from writing one response stream.
    lock=out/'writer.lock'
    with lock.open('x',encoding='utf-8') as f:f.write('active')
    try:
        # Read resume state only after acquiring the lock: another writer may
        # have completed between model inspection and lock acquisition.
        if (out/'run.json').exists():assert read_json(out/'run.json')==run_protocol,'Resume protocol mismatch'
        else:write_json(out/'run.json',run_protocol)
        completed={}
        if (out/'responses.jsonl').exists():
            for line in (out/'responses.jsonl').open(encoding='utf-8'):
                r=json.loads(line);key=(r['query_id'],r['condition_id'],r['seed'])
                assert key not in completed,'Duplicate resume key'
                assert r['response_sha256']==sha_text(r['response']),'Response hash mismatch'
                completed[key]=r
        for (q,c,seed),payload in zip(selected,jobs):
            if (q,c,seed) in completed:
                assert completed[(q,c,seed)]['prompt_sha256']==sha_text(payload['prompt']);continue
            req=urllib.request.Request(args.endpoint+'/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=300) as f:response=json.load(f)
            if response.get('error') or not response.get('done'):raise RuntimeError(response)
            r={'model_code':args.model,'dataset':data[q]['dataset'],'query_id':q,'condition_id':c,'seed':seed,'response':response['response'],'response_sha256':sha_text(response['response']),'prompt_sha256':sha_text(payload['prompt']),'model_digest':match['digest']}
            with (out/'responses.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            print(len(completed)+1,q,c,seed,flush=True);completed[(q,c,seed)]=r
    finally:lock.unlink()
if __name__=='__main__':main()
