"""Rebuild manuscript Figures 6-10 and 12-13 from package-local evidence."""
from pathlib import Path
from collections import defaultdict
import gzip, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'code/common.py').is_file())
PKG=ROOT
ART=HERE/'figures'
ART.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):return p
def readjson(p):
    if p.name=='expected_asr.json' and (ROOT/'output/asr.json').exists():
        return json.loads((ROOT/'output/asr.json').read_text(encoding='utf-8'))
    if p.name=='expected_ordering.json' and (ROOT/'output/asr.json').exists():
        v=json.loads((ROOT/'output/asr.json').read_text(encoding='utf-8'))['ordering']
        return [dict(cell_id=c,k=c.split('_')[1][1:],pattern=c.split('_')[2],
                     records=x['records'],asr_pp=x['asr_pp'],**x['per_model_pp']) for c,x in v.items()]
    return json.loads(p.read_text(encoding='utf-8'))
def readcsv(p):return pd.read_csv(p)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
    'axes.titlesize':10,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
    'legend.fontsize':8.5,'axes.linewidth':.7,'lines.linewidth':1.4,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
DIV=LinearSegmentedColormap.from_list('difference',['#326DA8','#FAFAF7','#DB631F'])
SEQ=LinearSegmentedColormap.from_list('asr',['#F4F8FC','#A7C7E2','#326DA8','#153A61'])
MODEL_IDS=['qwen35_9b','llama31_8b','mistral_7b','qwen3_1_7b','qwen3_4b','qwen3_8b','llama32_3b','gemma3_4b']
MODEL_NAMES=['Qwen3.5 9B','Llama 3.1 8B','Mistral 7B','Qwen3 1.7B','Qwen3 4B','Qwen3 8B','Llama 3.2 3B','Gemma 3 4B']
FIGURES={}

def heat(ax,arr,xlabels,ylabels,norm,cmap,fmt,rotation=0):
    assert np.nanmin(arr)>=norm.vmin and np.nanmax(arr)<=norm.vmax, 'Color scale clips measured values'
    mesh=ax.pcolormesh(np.arange(arr.shape[1]+1),np.arange(arr.shape[0]+1),arr,
        cmap=cmap,norm=norm,edgecolors='white',linewidth=.7,rasterized=False)
    ax.set_xticks(np.arange(arr.shape[1])+.5,xlabels,rotation=rotation,ha='right' if rotation else 'center')
    ax.set_yticks(np.arange(arr.shape[0])+.5,ylabels)
    ax.set_ylim(arr.shape[0],0);ax.tick_params(length=0,pad=5)
    for s in ax.spines.values():s.set_visible(False)
    for (i,j),v in np.ndenumerate(arr):
        rgb=np.array(cmap(norm(v))[:3]);lum=float(rgb@np.array([.2126,.7152,.0722]))
        ax.text(j+.5,i+.5,fmt.format(v),ha='center',va='center',fontsize=8.5,color='white' if lum<.52 else '#17232D')
    return mesh

def colorbar(fig,mesh,cax,label,ticks=None):
    cb=fig.colorbar(mesh,cax=cax,ticks=ticks);cb.set_label(label);cb.outline.set_visible(False)
    cb.solids.set_rasterized(False)
    cb.solids.set_edgecolor('face')  # Avoid white seams between vector colorbar cells.
    cb.ax.tick_params(length=2,width=.6,labelsize=8.5)

def savefig(fig,name,df,sources):
    fig.canvas.draw()
    # Bounds check for every visible text object, in physical figure coordinates.
    from matplotlib.text import Text
    renderer=fig.canvas.get_renderer();bounds=fig.bbox
    clipped=[]
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text():
            b=t.get_window_extent(renderer)
            if b.x0<-.5 or b.y0<-.5 or b.x1>bounds.width+.5 or b.y1>bounds.height+.5:clipped.append(t.get_text())
    assert not clipped,(name,clipped)
    for ext in ['pdf','svg','png']:fig.savefig(ART/f'{name}.{ext}',dpi=600)
    df.to_csv(ART/f'{name}.csv',index=False,float_format='%.9f',encoding='utf-8')
    FIGURES[name]={'source':sources,'rows':len(df),'width_in':fig.get_figwidth(),'height_in':fig.get_figheight(),
        'png_dpi':600,'all_text_within_canvas':True,'pdf_sha256':sha(ART/f'{name}.pdf')}
    plt.close(fig)

def build_figures():
    expected=readjson(PKG/'results/expected_asr.json')
    ordering=readjson(PKG/'results/expected_ordering.json')
    rows=[]
    for model in MODEL_IDS:
        for env in ['natural','answer_bearing']:
            for comparator in ['C00','C42']:
                a=expected[env]['C06']['per_model_pp'][model];b=expected[env][comparator]['per_model_pp'][model]
                rows.append({'model':model,'environment':env,'comparison':'CE-PR' if comparator=='C00' else 'CE-CR','ce_asr_pp':a,'comparator_asr_pp':b,'difference_pp':a-b,'responses_per_method_model':900})
    df=pd.DataFrame(rows);arr=df.difference_pp.to_numpy().reshape(8,4)
    fig=plt.figure(figsize=(5.5,4.35));ax=fig.add_axes([.25,.15,.58,.70]);cax=fig.add_axes([.865,.15,.022,.70])
    mesh=heat(ax,arr,['CE - PR','CE - CR','CE - PR','CE - CR'],MODEL_NAMES,TwoSlopeNorm(vmin=-50,vcenter=0,vmax=50),DIV,'{:+.1f}')
    ax.axvline(2,color='white',linewidth=3)
    ax.text(.25,1.035,'Irrelevant',transform=ax.transAxes,ha='center',fontweight='bold')
    ax.text(.75,1.035,'Answer-bearing',transform=ax.transAxes,ha='center',fontweight='bold')
    fig.suptitle('Single-poison differences across models',y=.97,fontsize=10,fontweight='bold')
    fig.text(.54,.05,'CE: Claim-Evidence   PR: PoisonedRAG   CR: CorruptRAG-AS',ha='center',fontsize=8.5)
    colorbar(fig,mesh,cax,'ASR difference (pp)',[-50,-25,0,25,50])
    savefig(fig,'local_model_heterogeneity',df,['results/expected_asr.json'])

    rows=[]
    for model in MODEL_IDS:
        for m in range(1,6):
            ce=expected['count'][f'C_K{m}']['per_model_pp'][model];pr=expected['count'][f'O_K{m}']['per_model_pp'][model]
            rows.append({'model':model,'m':m,'ce_asr_pp':ce,'pr_asr_pp':pr,'difference_pp':ce-pr,'responses_per_method_model':900})
    df=pd.DataFrame(rows)
    fig=plt.figure(figsize=(5.5,4.05));ax=fig.add_axes([.25,.17,.58,.69]);cax=fig.add_axes([.865,.17,.022,.69])
    arr=df.difference_pp.to_numpy().reshape(8,5)
    mesh=heat(ax,arr,range(1,6),MODEL_NAMES,TwoSlopeNorm(vmin=-50,vcenter=0,vmax=50),DIV,'{:+.1f}')
    ax.set_xlabel('Number of poisoned documents, $m$',labelpad=9)
    fig.suptitle('Claim-Evidence minus PoisonedRAG',y=.96,fontsize=10,fontweight='bold')
    colorbar(fig,mesh,cax,'ASR difference (pp)',[-50,-25,0,25,50])
    savefig(fig,'local_count_heterogeneity',df,['results/expected_asr.json: count'])

    orderdf=pd.DataFrame(ordering);orderdf['m']=orderdf.k.astype(int)
    assert orderdf.groupby('m').size().to_dict()=={1:5,2:10,3:10,4:5}
    for m,part in orderdf.groupby('m'):
        assert all(p.count('P')==m and len(p)==5 for p in part.pattern)
        assert np.allclose(part[MODEL_IDS].astype(float).mean(axis=1),part.asr_pp.astype(float),atol=1e-5)
    def order_panel(ax,part):
        arr=part[MODEL_IDS+['asr_pp']].astype(float).to_numpy()
        mesh=heat(ax,arr,MODEL_NAMES+['Overall'],part.pattern,Normalize(vmin=0,vmax=100),SEQ,'{:.1f}',rotation=55)
        ax.axvline(8,color='#54616B',linewidth=1.1)
        ax.set_ylabel('Context pattern $\\pi$')
        return mesh
    fig=plt.figure(figsize=(5.5,5.60))
    for i,m in enumerate([1,4]):
        ax=fig.add_axes([.17,.63 if i==0 else .23,.66,.26]);mesh=order_panel(ax,orderdf[orderdf.m==m])
        if i==0:ax.tick_params(labelbottom=False)
        ax.set_title(('(a) One poisoned document' if m==1 else '(b) Four poisoned documents'),pad=10,fontweight='bold')
    cax=fig.add_axes([.858,.23,.018,.66]);colorbar(fig,mesh,cax,'ASR (%)',[0,25,50,75,100])
    fig.suptitle('Claim-Evidence: all arrangements for $m=1$ and $m=4$',y=.974,fontsize=10,fontweight='bold')
    fig.text(.50,.025,'P: poisoned document    B: benign document',ha='center',fontsize=8.5)
    savefig(fig,'local_arrangements_m1_m4',orderdf[orderdf.m.isin([1,4])],['results/expected_ordering.json: m=1 and m=4 (10 patterns)'])
    for m in [2,3]:
        fig=plt.figure(figsize=(5.5,4.70));ax=fig.add_axes([.17,.27,.66,.59]);cax=fig.add_axes([.858,.27,.018,.59])
        mesh=order_panel(ax,orderdf[orderdf.m==m]);colorbar(fig,mesh,cax,'ASR (%)',[0,25,50,75,100])
        fig.suptitle(f'Claim-Evidence: all 10 arrangements for $m={m}$',y=.96,fontsize=10,fontweight='bold')
        fig.text(.50,.03,'P: poisoned document    B: benign document',ha='center',fontsize=8.5)
        savefig(fig,f'local_arrangements_m{m}',orderdf[orderdf.m==m],[f'results/expected_ordering.json: m={m} (10 patterns)'])

    paired=readcsv(PKG/'paper_assets/commercial_appendix/data/paired.csv')
    models=list(paired[['model_id','service']].drop_duplicates().itertuples(index=False,name=None))
    fig,axes=plt.subplots(1,3,figsize=(5.5,3.0),sharex=True,sharey=True)
    fig.subplots_adjust(left=.10,right=.985,bottom=.19,top=.77,wspace=.12)
    for ax,(mid,name) in zip(axes,models):
        part=paired[paired.model_id==mid].sort_values('k');x=part.difference_pp.to_numpy();y=part.k.to_numpy()
        ax.errorbar(x,y,xerr=[x-part.ci_low_pp.to_numpy(),part.ci_high_pp.to_numpy()-x],fmt='o',color='#DB631F',ecolor='#7E4D30',markersize=4,capsize=3,elinewidth=1)
        ax.axvline(0,color='#707A83',linewidth=.7,linestyle='--');ax.set_yticks(range(1,6));ax.set_ylim(5.5,.5);ax.set_xlim(-15,42);ax.set_xticks([-10,0,20,40]);ax.grid(axis='x',color='#DEE2E5',linewidth=.5);ax.set_axisbelow(True)
        ax.set_title(name.replace('DeepSeek V4.1 Flash','DeepSeek V4.1\nFlash'),fontsize=9,pad=7)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Poison count, $m$');fig.supxlabel('Paired ASR difference (pp)',y=.025,fontsize=9)
    fig.suptitle('Commercial paired effects with pointwise 95% CIs',y=.97,fontsize=10,fontweight='bold')
    savefig(fig,'commercial_paired_intervals',paired,['paper_assets/commercial_appendix/data/paired.csv (15 frozen intervals)'])

    ladder=readcsv(PKG/'paper_assets/commercial_appendix/data/ladder.csv')
    # Verify saved stratification against every frozen response using the unchanged scorer.
    spec=importlib.util.spec_from_file_location('frozen_scorer',track(PKG/'code/official_scorer.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    inputs=track(PKG/'data/inputs.jsonl.gz')
    with gzip.open(inputs,'rt',encoding='utf-8') as f:targets={(r['dataset'],r['query_id']):r['target_answer'] for r in map(json.loads,f)}
    counts=defaultdict(lambda:[0,0,0]);completed=0;missing=0
    with gzip.open(track(PKG/'results/responses/commercial.jsonl.gz'),'rt',encoding='utf-8') as f:
        for r in map(json.loads,f):
            key=(r['model_id'],r['dataset'],int(r['k']),r['method']);counts[key][2]+=1
            if r['status']=='completed':
                counts[key][1]+=1;counts[key][0]+=int(module.official_attack_success(targets[r['dataset'],r['query_id']],r['final_answer']));completed+=1
            else:missing+=1
    sub=pd.DataFrame([dict(model_id=mid,dataset=ds,k=k,method=method,
                         hits=h,valid_n=n,planned_n=p,missing=p-n,asr_pct=100*h/n)
                      for (mid,ds,k,method),(h,n,p) in sorted(counts.items())])
    assert len(sub)==90 and completed==1798 and missing==2
    for r in sub.itertuples():
        h,n,p=counts[(r.model_id,r.dataset,r.k,r.method)]
        assert (h,n,p)==(r.hits,r.valid_n,r.planned_n)
        assert abs(100*h/n-r.asr_pct)<1e-7
    for r in ladder.itertuples():
        for m in range(1,6):
            part=sub[(sub.model_id==r.model_id)&(sub.method==r.method)&(sub.k==m)]
            assert part.hits.sum()==getattr(r,f'k{m}_hits') and part.valid_n.sum()==getattr(r,f'k{m}_n')
    fig,axes=plt.subplots(3,3,figsize=(5.5,5.55),sharex=True,sharey=True)
    fig.subplots_adjust(left=.11,right=.985,bottom=.15,top=.87,hspace=.39,wspace=.14)
    for row,(mid,name) in enumerate(models):
        for col,(dataset,dlabel) in enumerate([('nq','NQ'),('hotpotqa','HotpotQA'),('msmarco','MS MARCO')]):
            ax=axes[row,col]
            for method,label,color,marker,style in [('original','PoisonedRAG','#326DA8','o','-'),('claim_evidence','Claim-Evidence','#DB631F','s','--')]:
                part=sub[(sub.model_id==mid)&(sub.dataset==dataset)&(sub.method==method)].sort_values('k')
                ax.plot(part.k,part.asr_pct,color=color,marker=marker,linestyle=style,markersize=3,label=label,clip_on=False)
                absent=part[part.missing>0]
                if len(absent):ax.scatter(absent.k,absent.asr_pct,marker='*',s=50,color=color,edgecolor='white',linewidth=.5,zorder=5)
            ax.set_ylim(0,100);ax.set_xlim(.7,5.3);ax.set_xticks(range(1,6));ax.set_yticks([0,50,100]);ax.grid(axis='y',color='#DEE2E5',linewidth=.5);ax.spines[['top','right']].set_visible(False)
            if row==0:ax.set_title(dlabel,pad=6,fontweight='bold',fontsize=9)
            if col==0:ax.text(0,1.10,name,transform=ax.transAxes,fontsize=8.5,ha='left') if row else ax.text(0,1.37,name,transform=ax.transAxes,fontsize=8.5,ha='left')
    fig.suptitle('Commercial ASR by dataset',y=.98,fontsize=10,fontweight='bold')
    fig.supylabel('ASR (%)',x=.015,fontsize=9);fig.supxlabel('Number of poisoned documents, $m$',y=.085,fontsize=9)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.53,.005),ncol=2,frameon=False)
    savefig(fig,'commercial_dataset_ladders',sub,['results/responses/commercial.jsonl.gz: 1798 valid and 2 missing records independently checked','paper_assets/commercial_appendix/data/ladder.csv: 30 totals matched'])
    return {'all_ordering_patterns':30,'ordering_model_and_overall_cells':270,'frozen_commercial_interval_rows':15,'commercial_dataset_cells_checked':90,'commercial_responses_rescored':1798,'commercial_missing':2,'commercial_overall_cells_matched':30,'new_model_calls':0,'new_inference':0}

if __name__=='__main__':
    checks=build_figures()
    (HERE/'figure_checks.json').write_text(json.dumps({'checks':checks,'figures':FIGURES},indent=2)+'\n',encoding='utf-8')
    print('Seven appendix figures rebuilt; all 30 orderings and 90 commercial dataset cells checked.')
