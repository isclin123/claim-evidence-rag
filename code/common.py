"""Package-local data, context assembly and scoring. No network on import."""
from pathlib import Path
import gzip
import hashlib
import itertools
import json

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ['nq', 'hotpotqa', 'msmarco']
MODELS = ['qwen35_9b','llama31_8b','mistral_7b','qwen3_1_7b',
          'qwen3_4b','qwen3_8b','llama32_3b','gemma3_4b']
METHODS = {'C00':'PoisonedRAG','C06':'Claim-Evidence','C42':'CorruptRAG-AS'}
BATCHES = ['natural','answer_bearing','count','position','ordering']
SEEDS = [101,202,303]
EXPECTED = dict(zip(BATCHES,[21600,21600,72000,64800,216000]))

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def read_rows(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def inputs():
    return {r['query_id']:r for r in read_rows(ROOT/'data/inputs.jsonl.gz')}

def responses(batch):
    return read_rows(ROOT/f'results/responses/{batch}.jsonl.gz')

def sha_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def cell_spec(batch, cell):
    if batch in ['natural','answer_bearing']:
        if cell not in METHODS: raise ValueError(cell)
        return cell, 'PBBBB'
    if batch=='count':
        prefix, k=cell.split('_K'); k=int(k)
        if prefix not in ['O','C'] or not 1<=k<=5: raise ValueError(cell)
        return {'O':'C00','C':'C06'}[prefix], 'P'*k+'B'*(5-k)
    if batch=='position':
        method,p=cell.split('@p'); p=int(p)
        if method not in METHODS or p not in [1,3,5]:raise ValueError(cell)
        return method, 'B'*(p-1)+'P'+'B'*(5-p)
    if batch=='ordering':
        method,k,pattern=cell.split('_'); count=int(k[1:])
        if method!='C06' or len(pattern)!=5 or set(pattern)!={'B','P'} or pattern.count('P')!=count:raise ValueError(cell)
        return method,pattern
    raise ValueError(batch)

def cells(batch):
    if batch in ['natural','answer_bearing']:return list(METHODS)
    if batch=='count':return [f'{m}_K{k}' for m in ['O','C'] for k in range(1,6)]
    if batch=='position':return [f'{m}@p{p}' for m in METHODS for p in [1,3,5]]
    if batch=='ordering':
        return [f'C06_K{k}_'+''.join('P' if i in ix else 'B' for i in range(5))
                for k in range(1,5) for ix in itertools.combinations(range(5),k)]
    raise ValueError(batch)

def contexts(row,batch,cell):
    method,pattern=cell_spec(batch,cell)
    poison=iter(row['documents'][method])
    benign=iter(row['benign_natural' if batch=='natural' else 'benign_answer_bearing'])
    return [next(poison) if s=='P' else next(benign) for s in pattern]

def prompt(row,batch,cell,protocol):
    return protocol['prompt_template'].format(question=row['question'],contexts='\n'.join(contexts(row,batch,cell)))

def request(row,batch,cell,seed,model,protocol):
    return {'model':model,'prompt':prompt(row,batch,cell,protocol),
            'system':protocol['system_prompt'],'stream':False,'think':protocol['think'],
            'keep_alive':protocol['keep_alive'],
            'options':{'temperature':protocol['temperature'],'seed':seed,
                       'num_predict':protocol['max_output_tokens'],'num_ctx':protocol['num_ctx']}}

def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
