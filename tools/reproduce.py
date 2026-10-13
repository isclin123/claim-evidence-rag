"""Rescore frozen responses, check paper values and optionally recompute inference."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import numpy as np
from common import *
from official_scorer import official_attack_success, clean_str
import statistics_core as st

def close(a,b,tol=1.1e-6):
    assert np.allclose(a,b,atol=tol,rtol=0,equal_nan=True),(a,b)

def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def score_batch(batch,data):
    cs=cells(batch);qs=sorted(data,key=lambda q:(DATASETS.index(data[q]['dataset']),q))
    qi={q:i for i,q in enumerate(qs)};mi={m:i for i,m in enumerate(MODELS)};ci={c:i for i,c in enumerate(cs)}
    full=np.full((300,8,len(cs),3),np.nan)
    for r in responses(batch):
        key=(qi[r['query_id']],mi[r['model_code']],ci[r['condition_id']],SEEDS.index(r['seed']))
        assert np.isnan(full[key]),('duplicate',batch,key)
        full[key]=official_attack_success(data[r['query_id']]['target_answer'],r['response'])
    assert np.isfinite(full).all(),batch
    cube=full.mean(axis=3);gi=np.array([DATASETS.index(data[q]['dataset']) for q in qs])
    summary={}
    for c,i in ci.items():
        arr=full[:,:,i,:]
        summary[c]={'records':int(arr.size),'hits':int(arr.sum()),'asr_pp':round(100*float(arr.mean()),6),
                    'per_model_pp':{m:round(100*float(arr[:,j].mean()),6) for m,j in mi.items()},
                    'per_dataset_pp':{d:round(100*float(arr[gi==g].mean()),6) for g,d in enumerate(DATASETS)}}
    return summary,cube,gi,cs

def validate_asset_points(all_results,data):
    a=ROOT/'paper_assets'
    for r in csv_rows(a/'method_asr/data/asr.csv'):
        b={'irrelevant':'natural','answer_bearing':'answer_bearing'}[r['setting']]
        close(all_results[b][r['condition']]['asr_pp'],float(r['asr_pp']))
    for r in csv_rows(a/'method_asr/data/by_dataset.csv'):
        b={'irrelevant':'natural','answer_bearing':'answer_bearing'}[r['setting']]
        close(all_results[b][r['condition']]['per_dataset_pp'][r['dataset']],float(r['asr_pp']))
    for r in csv_rows(a/'defense_drop/data/asr.csv'):
        b={'natural':'natural','defended':'answer_bearing'}[r['setting']]
        close(all_results[b][r['construction_id']]['asr_pp'],float(r['asr_percent']))
    for r in csv_rows(a/'count_ladder/data/ladder.csv'):
        c={'C00':'O','C06':'C'}[r['condition']]+'_K'+r['k'];close(all_results['count'][c]['asr_pp'],float(r['asr_pp']))
    for r in csv_rows(a/'count_ladder/data/per_model_gap.csv'):
        k=r['k'];m=r['model'];o=all_results['count']['O_K'+k]['per_model_pp'][m];c=all_results['count']['C_K'+k]['per_model_pp'][m]
        close([o,c,c-o],[float(r[x]) for x in ['poisonedrag_pp','claim_evidence_pp','gap_pp']],2e-6)
    for r in csv_rows(a/'position_effect/data/positions.csv'):
        close(all_results['position'][r['condition']+'@'+r['position']]['asr_pp'],float(r['asr_pp']))
    for r in csv_rows(a/'position_effect/data/orderings.csv'):
        close(all_results['ordering']['C06_K'+r['k']+'_'+r['pattern']]['asr_pp'],float(r['asr_pp']))
    coverage={}
    for ds in DATASETS+['all']:
        rr=[r for r in data.values() if ds=='all' or r['dataset']==ds]
        v={}
        for setting,key in [('irrelevant','benign_natural'),('answer_bearing','benign_answer_bearing')]:
            counts=[sum(clean_str(r['correct_answer']) in clean_str(d) for d in r[key]) for r in rr]
            v[setting]=sum(counts)/len(counts)
        coverage[ds]=v
    for r in csv_rows(a/'benign_coverage/data/coverage.csv'):
        for setting in ['irrelevant','answer_bearing']:close(coverage[r['dataset']][setting],float(r[setting+'_mean']),5.1e-5)
    return coverage

def skip_signs(rng,sizes):
    for n in sizes:
        for i in range(0,100000,5000):rng.choice((-1.,1.),size=(min(5000,100000-i),n,1))

def inference(batch,cube,gi,cs,families):
    result={};specs=[]
    if batch=='count':
        specs=[('D4-method',[(f'c06_minus_original_k{k}',{f'C_K{k}':1.,f'O_K{k}':-1.}) for k in range(1,6)],[])]
    if batch=='position':
        specs=[('E1-position',[(f'position_{m}_p{p}',{f'{m}@p{p}':1.,f'{m}@p1':-1.}) for m in ['C06','C42'] for p in [3,5]],[]),
               ('E1-baseline-position',[(f'position_C00_p{p}',{f'C00@p{p}':1.,'C00@p1':-1.}) for p in [3,5]],[300,300,300,300,100,100,100])]
    if batch=='ordering':
        specs=[('E3-front-tail',[(f'E3_K{k}_'+('B'*(5-k)+'P'*k)+'_minus_'+('P'*k+'B'*(5-k)),
                   {f'C06_K{k}_'+('B'*(5-k)+'P'*k):1.,f'C06_K{k}_'+('P'*k+'B'*(5-k)):-1.}) for k in range(1,5)],[])]
    if not specs:return result
    boot=st.bootstrap_cell_means(cube,gi,3,10000,2026082601)
    for name,spec,skip in specs:
        frozen=families[name];labels=[s[0] for s in spec];w=np.zeros((len(cs),len(labels)))
        for j,(_,terms) in enumerate(spec):
            for c,v in terms.items():w[cs.index(c),j]=v
        values=np.einsum('cmk,kt->cmt',cube,w).mean(axis=1)
        draws=np.einsum('bmk,kt->bmt',boot,w).mean(axis=1)
        point=st.dataset_equal_mean(values,gi,3);se=draws.std(axis=0,ddof=1)
        rng=np.random.default_rng(2026082602);skip_signs(rng,skip)
        tests=st.studentized_signflip_many(values,gi,3,rng,100000)
        pp={label:t['p_perm'] for label,t in zip(labels,tests)}|frozen['auxiliary_p_values']
        adjusted,_=st.holm_adjust_pvalues(pp[k] for k in frozen['holm_order'])
        adj=dict(zip(frozen['holm_order'],adjusted));items={}
        critical=frozen['simultaneous_critical_value']
        if not frozen['auxiliary_p_values']:
            computed=np.percentile(np.max(np.abs(draws-point)/se,axis=1),95)
            close(computed,critical,1e-6)
        for j,label in enumerate(labels):
            f=frozen['items'][label]
            val={'effect_pp':round(100*float(point[j]),6),
                 'pointwise_ci_95_pp':[round(float(x)*100,6) for x in np.percentile(draws[:,j],[2.5,97.5])],
                 'se_pp':round(100*float(se[j]),6),'p_perm':tests[j]['p_perm'],'holm_adjusted_p':adj[label],
                 'simultaneous_ci_95_pp':[100*float(point[j]-critical*se[j]),100*float(point[j]+critical*se[j])]}
            for key in ['effect_pp','pointwise_ci_95_pp','se_pp']:close(val[key],f[key])
            for key in ['p_perm','holm_adjusted_p']:close(val[key],f[key],1e-12)
            close(val['simultaneous_ci_95_pp'],f['simultaneous_ci_95_pp'],5e-6)
            items[label]=val
        result[name]={'items':items,'original_family_size':frozen['items_tested'],
                     'full_family_calibration_recomputed':not bool(frozen['auxiliary_p_values'])}
        print(name, len(items),'reported contrasts match',flush=True)
    return result

def commercial(data,statistics):
    rows=list(responses('commercial'));table={};scored={}
    for r in rows:
        hit=None if r['status']!='completed' else int(official_attack_success(data[r['query_id']]['target_answer'],r['final_answer']))
        scored[(r['model_id'],r['sample_id'],r['method'],r['k'])]=hit
    for mid in ['M01','M02','M03']:
        for method in ['original','claim_evidence']:
            for k in range(1,6):
                hits=[v for (m,_,me,kk),v in scored.items() if (m,me,kk)==(mid,method,k) and v is not None]
                table[(mid,method,k)]={'hits':sum(hits),'n':len(hits),'asr_pp':100*sum(hits)/len(hits)}
    for r in csv_rows(ROOT/'paper_assets/commercial_appendix/data/ladder.csv'):
        for k in range(1,6):
            v=table[(r['model_id'],r['method'],k)]
            assert v['hits']==int(r[f'k{k}_hits']) and v['n']==int(r[f'k{k}_n'])
            close(v['asr_pp'],float(r[f'k{k}_asr_pp']),5.1e-5)
    paired=[]
    if statistics:
        from scipy.stats import binomtest
        samples=read_json(ROOT/'data/commercial_sample.json')['rows']
        ids=[r['sample_id'] for d in DATASETS for r in samples if r['dataset']==d]
        rng=np.random.default_rng(20260914)
        draws=np.concatenate([rng.integers(j*20,(j+1)*20,size=(10000,20)) for j in range(3)],axis=1)
        for mid in ['M01','M02','M03']:
            for k in range(1,6):
                def arr(method):return np.array([np.nan if scored[(mid,s,method,k)] is None else scored[(mid,s,method,k)] for s in ids])
                a,b=arr('original'),arr('claim_evidence');d=b-a;ok=np.isfinite(d)
                gain=int(((a==0)&(b==1)).sum());loss=int(((a==1)&(b==0)).sum())
                lo,hi=np.percentile(100*np.nanmean(d[draws],axis=1),[2.5,97.5])
                paired.append({'model_id':mid,'k':k,'pair_n':int(ok.sum()),'gains':gain,'losses':loss,
                               'difference_pp':100*float(np.nanmean(d)),'ci_low_pp':float(lo),'ci_high_pp':float(hi),
                               'p_exact_mcnemar':float(binomtest(gain,gain+loss,.5).pvalue) if gain+loss else 1.})
        adj15,_=st.holm_adjust_pvalues(r['p_exact_mcnemar'] for r in paired)
        adj25,_=st.holm_adjust_pvalues([r['p_exact_mcnemar'] for r in paired]+[1.]*10)
        frozen={(r['model_id'],int(r['k'])):r for r in csv_rows(ROOT/'paper_assets/commercial_appendix/data/paired.csv')}
        for i,r in enumerate(paired):
            r.update(p_holm15=adj15[i],p_holm25=adj25[i]);f=frozen[(r['model_id'],r['k'])]
            for key in ['pair_n','gains','losses','difference_pp','ci_low_pp','ci_high_pp','p_exact_mcnemar','p_holm15','p_holm25']:close(r[key],float(f[key]),5.1e-5 if key in ['difference_pp','ci_low_pp','ci_high_pp'] else 1e-12)
        print('commercial: all 15 paired comparisons, both Holm families match',flush=True)
    return {'asr':[dict(model=m,method=me,k=k,**v) for (m,me,k),v in table.items()],'paired':paired,'valid':1798,'blocked':2}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--statistics',action='store_true');ap.add_argument('--figures',action='store_true');args=ap.parse_args()
    data=inputs();expected=read_json(ROOT/'results/expected_asr.json');families=read_json(ROOT/'results/statistical_families.json')
    result={};stats={}
    for batch in BATCHES:
        s,cube,gi,cs=score_batch(batch,data);result[batch]=s
        if batch!='ordering':
            assert set(s)==set(expected[batch])
            for c,entry in s.items():
                f=expected[batch][c];assert entry['records']==f['records'];close(entry['asr_pp'],f['asr_pp'])
                for key in ['per_model_pp','per_dataset_pp']:
                    for label,value in entry[key].items():close(value,f[key][label])
        else:
            for f in read_json(ROOT/'results/expected_ordering.json'):
                entry=s[f['cell_id']];close(entry['asr_pp'],float(f['asr_pp']))
                for m in MODELS:close(entry['per_model_pp'][m],float(f[m]))
        print(batch,'all ASRs match frozen source',flush=True)
        if args.statistics:stats.update(inference(batch,cube,gi,cs,families))
    coverage=validate_asset_points(result,data)
    comm=commercial(data,args.statistics)
    write_json(ROOT/'output/asr.json',result);write_json(ROOT/'output/coverage.json',coverage)
    write_json(ROOT/'output/commercial.json',comm)
    if args.statistics:
        write_json(ROOT/'output/inference.json',stats)
        subprocess.run([sys.executable,str(ROOT/'tools/posthoc_position_contrast.py')],check=True)
        # Every retained appendix row uses the full eight-model panel.
        posthoc={r['position']:r for r in csv_rows(ROOT/'output/posthoc_position.csv')}
        for r in csv_rows(ROOT/'paper_assets/method_ci/data/contrasts.csv'):
            assert int(r['models'])==len(MODELS)
            if r['family']=='D4-method':
                v=stats['D4-method']['items']['c06_minus_original_k1']
                close([v['effect_pp'],*v['pointwise_ci_95_pp']], [float(r[k]) for k in ['effect_pp','pw_low','pw_high']])
                close(v['holm_adjusted_p'],float(r['holm_p']),1e-10)
            else:
                assert r['family']=='posthoc-closest-by-position'
                position={'$\\pi$ = PBBBB':'p1','$\\pi$ = BBPBB':'p3','$\\pi$ = BBBBP':'p5'}[r['label']]
                v=posthoc[position]
                close([float(v[k]) for k in ['effect_pp','pw_low','pw_high']],
                      [float(r[k]) for k in ['effect_pp','pw_low','pw_high']],5.1e-5)
                close(float(v['holm_p']),float(r['holm_p']),1e-8)
        for r in csv_rows(ROOT/'paper_assets/count_ladder/data/contrasts.csv'):
            v=stats['D4-method']['items']['c06_minus_original_k'+r['k']]
            close([v['effect_pp'],*v['pointwise_ci_95_pp']], [float(r[k]) for k in ['effect_pp','pw_low','pw_high']])
            close(v['holm_adjusted_p'],float(r['holm_p']),1e-10)
        for r in csv_rows(ROOT/'paper_assets/position_effect/data/contrasts.csv'):
            if r['batch']=='position':
                method={v:k for k,v in METHODS.items()}[r['construction']]
                position=3 if r['contrast'].startswith('BBPBB') else 5
                label=f'position_{method}_p{position}'
            else:
                label=next(k for k in stats[r['family']]['items'] if k.startswith('E3_K'+r['k']+'_'))
            v=stats[r['family']]['items'][label]
            close([v['effect_pp'],*v['pointwise_ci_95_pp']], [float(r[k]) for k in ['effect_pp','pw_low','pw_high']])
            close(v['holm_adjusted_p'],float(r['holm_p']),1e-10)
    if args.figures:
        subprocess.run([sys.executable,str(ROOT/'tools/rebuild_assets.py')],check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/verify_paper_outputs.py')],check=True)
    write_json(ROOT/'output/reproduction_report.json',{'passed':True,'local_responses':396000,'commercial_valid':1798,'commercial_blocked':2,'statistics_recomputed':args.statistics,'family_calibration':'Auxiliary p values and reduced-family simultaneous critical values are frozen inputs.'})
    print('PASS: manuscript numerical sources reproduced offline. Results are in output/.')
if __name__=='__main__':main()
