"""Rerun preliminary responses on local Ollama; offline dry run by default."""
import argparse
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *


def validate_resume(rows, data, panel, order, config, model):
    wanted = set(order)
    done = {}
    for row in rows:
        key = record_key(row)
        if key not in wanted or key in done:
            raise ValueError('Unexpected or duplicate resume key')
        if row['model_code'] != model or row['model_digest'] != panel[model]['digest']:
            raise ValueError('Resume model mismatch')
        if not isinstance(row['response'],str) or not row['response'].strip():
            raise ValueError('Empty resume response')
        if row['response_sha256'] != sha_text(row['response']):
            raise ValueError('Resume response hash mismatch')
        if row['prompt_sha256'] != sha_text(prompt(data[key[:2]],key[2],config)):
            raise ValueError('Resume prompt hash mismatch')
        done[key] = row
    return done


def main():
    panel = models()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model',choices=list(panel)+['all'],required=True)
    ap.add_argument('--limit',type=int)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--endpoint',default='http://127.0.0.1:11434')
    args = ap.parse_args()
    if args.limit is not None and args.limit < 1:
        ap.error('--limit must be positive')
    url = urllib.parse.urlparse(args.endpoint)
    if url.scheme != 'http' or url.hostname not in ['127.0.0.1','localhost','::1'] or url.username or url.password:
        ap.error('Use a local Ollama HTTP endpoint')
    endpoint = args.endpoint.rstrip('/')
    data,order,config = inputs(),schedule(),protocol()
    chosen = list(panel) if args.model == 'all' else [args.model]
    selected = order[:args.limit] if args.limit else order
    if not args.execute:
        first = selected[0]
        report = dict(models=chosen,requests_per_model=len(selected),total_requests=len(selected)*len(chosen),
                      first_key=first,first_request=request(data[first[:2]],first[2],first[3],panel[chosen[0]],config),
                      network_calls=0,model_calls=0)
        write_json(OUTPUT/'dry_run.json',report)
        print(f'Dry run: {report["total_requests"]} requests, zero model/network calls.')
        return
    with urllib.request.urlopen(endpoint+'/api/tags',timeout=30) as f:
        installed = {r['name']:r['digest'] for r in json.load(f)['models']}
    for name in chosen:
        if installed.get(panel[name]['tag']) != panel[name]['digest']:
            raise RuntimeError('Install the exact documented model: '+panel[name]['tag'])
    for name in chosen:
        out = OUTPUT/'reruns'/name
        out.mkdir(parents=True,exist_ok=True)
        lock = out/'writer.lock'
        with lock.open('x',encoding='utf-8') as f:
            f.write('active\n')
        try:
            frozen = dict(model=name,spec=panel[name],protocol=config,
                          inputs_sha256=sha_text(json.dumps(list(data.values()),sort_keys=True)),
                          schedule_sha256=sha_text(json.dumps(order)))
            if (out/'run.json').exists():
                if read_json(out/'run.json') != frozen:
                    raise RuntimeError('Resume configuration mismatch')
            else:
                write_json(out/'run.json',frozen)
            raw = out/'responses.jsonl'
            done = validate_resume(read_rows(raw) if raw.exists() else [],data,panel,order,config,name)
            for key in selected:
                if key in done:
                    continue
                ds,q,cid,seed = key
                payload = request(data[(ds,q)],cid,seed,panel[name],config)
                req = urllib.request.Request(endpoint+'/api/generate',data=json.dumps(payload).encode('utf-8'),
                                             headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=300) as f:
                    result = json.load(f)
                if result.get('error') or not result.get('done') or not str(result.get('response','')).strip():
                    raise RuntimeError('Incomplete or empty model response')
                row = dict(dataset=ds,query_id=q,condition_id=cid,seed=seed,model_code=name,
                           model_tag=panel[name]['tag'],status='ok',
                           model_digest=panel[name]['digest'],response=result['response'],
                           prompt_sha256=sha_text(payload['prompt']),response_sha256=sha_text(result['response']))
                with raw.open('a',encoding='utf-8') as f:
                    f.write(json.dumps(row,ensure_ascii=False)+'\n')
                    f.flush()
                done[key] = row
            print(name,len(done),'/',len(order),'responses')
        finally:
            lock.unlink()


if __name__ == '__main__':
    main()
