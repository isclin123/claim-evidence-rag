"""Validate the complete matrix and rescore the recorded response streams."""
from collections import Counter, defaultdict
from common import *
from constructions import construct
from official_scorer import official_attack_success, self_test


def evaluate(response_dir=None):
    assert self_test()['passed']
    data, panel, order, config = inputs(), models(), schedule(), protocol()
    assert len(data) == 300 and len(panel) == 8 and len(METHODS) == 14
    assert read_json(ROOT/'data/methods.json') == METHODS
    assert Counter(r['dataset'] for r in data.values()) == dict.fromkeys(DATASETS,100)
    assert config['response_seeds'] == SEEDS
    expected = {(ds,q,c,s) for ds,q in data for c in METHODS for s in SEEDS}
    assert len(order) == len(set(order)) == len(expected) == 12600
    assert set(order) == expected
    prompts = {}
    for key,row in data.items():
        assert set(row['poison']) == set(METHODS)
        assert len(row['benign']) == 4
        for cid in METHODS:
            assert construct(row,cid) == row['poison'][cid],(key,cid,'construction mismatch')
            prompts[(*key,cid)] = sha_text(prompt(row,cid,config))
    groups = defaultdict(lambda:[0,0])
    count = 0
    for model,spec in panel.items():
        seen = []
        path = (Path(response_dir)/model/'responses.jsonl' if response_dir is not None
                else ROOT/'results/responses'/f'{model}.jsonl.gz')
        for row in read_rows(path):
            key = record_key(row)
            assert key in expected and row['model_code'] == model
            assert row['model_tag'] == spec['tag'] and row['model_digest'] == spec['digest']
            assert row['status'] == 'ok' and isinstance(row['response'],str) and row['response'].strip()
            assert row['response_sha256'] == sha_text(row['response'])
            assert row['prompt_sha256'] == prompts[key[:3]]
            seen.append(key)
            ds,q,cid,_ = key
            hit = int(official_attack_success(data[(ds,q)]['target_answer'],row['response']))
            for m,d in [(model,ds),(model,'ALL'),('ALL',ds),('ALL','ALL')]:
                value = groups[(m,d,cid)]
                value[0] += hit
                value[1] += 1
            count += 1
        assert seen == order,(model,'missing, duplicated or reordered response')
    assert count == 100800
    results = []
    for (m,ds,cid),(hits,n) in groups.items():
        baseline = groups[(m,ds,'C00')]
        results.append(dict(model=m,dataset=ds,condition_id=cid,method=METHODS[cid],
                            successes=hits,total=n,asr=hits/n,
                            delta_vs_poisonedrag_pp=100*(hits/n-baseline[0]/baseline[1])))
    results.sort(key=lambda r:(r['model'],r['dataset'],-r['asr'],r['condition_id']))
    assert len(results) == 504
    if response_dir is None:
        frozen = {(r['model'],r['dataset'],r['condition_id']):r for r in read_json(ROOT/'results/expected_asr.json')}
        assert len(frozen) == 504
        for row in results:
            expected_row = frozen[(row['model'],row['dataset'],row['condition_id'])]
            for k in ['successes','total','method']:
                assert row[k] == expected_row[k],(k,row)
            for k in ['asr','delta_vs_poisonedrag_pp']:
                assert abs(row[k]-expected_row[k]) < 1e-12,(k,row)
    completion = read_json(ROOT/'results/completion.json')
    assert completion['status'] == 'COMPLETE' and completion['missing'] == 0
    assert completion['verified_unique_slots'] == completion['expected_slots'] == count
    assert completion['response_counts_by_model'] == dict.fromkeys(panel,12600)
    return results,dict(passed=True,methods=14,questions=300,models=8,seeds=3,
                       reconstructed_documents=4200,verified_responses=count,aggregate_rows=504)
