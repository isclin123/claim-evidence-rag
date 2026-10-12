"""Package-local preliminary inputs, requests and response records."""
import gzip
import hashlib
import json
from pathlib import Path
from constructions import METHODS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / 'output' / 'preliminary'
DATASETS = ['nq', 'hotpotqa', 'msmarco']
SEEDS = [101, 202, 303]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def inputs():
    return {(r['dataset'], r['query_id']): r for r in read_rows(ROOT / 'data/inputs.jsonl.gz')}


def protocol():
    return read_json(ROOT / 'data/protocol.json')


def models():
    return read_json(ROOT / 'data/models.json')


def schedule():
    return [tuple(r) for r in read_json(ROOT / 'data/schedule.json')]


def prompt(row, method, config=None):
    config = config or protocol()
    if method not in METHODS:
        raise ValueError('Unknown method')
    contexts = [row['poison'][method]] + row['benign']
    if len(contexts) != 5:
        raise ValueError('Expected five context documents')
    return config['prompt_template'].format(question=row['question'], contexts='\n'.join(contexts))


def request(row, method, seed, model, config=None):
    config = config or protocol()
    return dict(model=model['tag'], prompt=prompt(row, method, config),
                system=config['system_prompt'], stream=False, think=config['think'],
                keep_alive=config['keep_alive'], options=dict(
                    temperature=config['temperature'], seed=seed,
                    num_predict=config['max_output_tokens'], num_ctx=config['num_ctx']))


def record_key(row):
    return tuple(row[k] for k in ('dataset', 'query_id', 'condition_id', 'seed'))
