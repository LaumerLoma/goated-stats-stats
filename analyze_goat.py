"""Read-only reanalysis of supplied GOAT data; no input file is modified.

Extraction: bundled Python openpyxl -> /private/tmp/goat_rows.json.
Numerical execution: python with NumPy/SciPy, which supplies unavailable tests.
All permutations are two-sided by absolute statistic; fixed random seed.
"""
import itertools, json, math
from pathlib import Path
import numpy as np
from scipy import stats
import openpyxl

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'analysis_results.json'
wb=openpyxl.load_workbook(ROOT/'goat_dataset.xlsx',data_only=False)
cached=openpyxl.load_workbook(ROOT/'goat_dataset.xlsx',data_only=True)
headers=[c.value for c in wb['Data'][1]]
rows=[dict(zip(headers,[c.value for c in rr]),excel_row=rr[0].row) for rr in list(wb['Data'])[1:]]
for d in rows:
    d['H'] = d['GOAT titles']
    d['J'] = d['Best other titles']
    d['T'] = d['GOAT team titles']
    d['L'] = d['L (seasons or Games)']
    d['N'] = d['League N (players)']
    d['index'] = d['T']/d['H'] if d['T'] is not None else None
    d['margin'] = d['H']/d['J']-1 if d['J'] is not None else None
    d['open'] = int(d['League system']=='Open EU')
    d['female'] = int(d['Sex']=='F')

def holm(ps):
    ps=np.asarray(ps); order=np.argsort(ps); q=np.empty(len(ps))
    q[order]=np.minimum(1,np.maximum.accumulate(ps[order]*(len(ps)-np.arange(len(ps)))))
    return q.tolist()

def ols(y, X):
    y=np.asarray(y,float); X=np.asarray(X,float)
    if X.ndim==1: X=X[:,None]
    X=np.column_stack([np.ones(len(y)),X]); n,k=X.shape
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; rss=e@e
    inv=np.linalg.inv(X.T@X); se=np.sqrt(np.diag(inv)*rss/(n-k))
    p=2*stats.t.sf(np.abs(b/se),n-k)
    ci=np.column_stack([b-stats.t.ppf(.975,n-k)*se,b+stats.t.ppf(.975,n-k)*se])
    ll=-n/2*(np.log(2*np.pi)+1+np.log(rss/n)); aic=-2*ll+2*(k+1)
    aicc=aic+2*(k+1)*(k+2)/(n-k-2) if n>k+2 else None
    h=np.einsum('ij,jk,ik->i',X,inv,X)
    cov=inv@(X.T@((e/(1-h))[:,None]**2*X))@inv
    hcse=np.sqrt(np.diag(cov)); hcp=2*stats.t.sf(np.abs(b/hcse),n-k)
    loo=[]
    for i in range(n):
        mask=np.arange(n)!=i
        bb=np.linalg.lstsq(X[mask],y[mask],rcond=None)[0]
        loo.append((y[i]-X[i]@bb)**2)
    return dict(n=n,k=k,beta=b.tolist(),se=se.tolist(),p=p.tolist(),ci95=ci.tolist(),
                hc3_p=hcp.tolist(),rss=float(rss),aic=float(aic),aicc=aicc,
                loo_rmse=float(np.sqrt(np.mean(loo))))

def corr_exact(x,y,rank=True):
    x=np.asarray(x,float); y=np.asarray(y,float)
    r,p=stats.spearmanr(x,y) if rank else stats.pearsonr(x,y)
    xx=stats.rankdata(x) if rank else x
    yy=stats.rankdata(y) if rank else y
    xx=(xx-xx.mean())/np.linalg.norm(xx-xx.mean())
    yy=(yy-yy.mean())/np.linalg.norm(yy-yy.mean())
    vals=np.array([xx@yy[list(ix)] for ix in itertools.permutations(range(len(x)))])
    return dict(n=len(x),r=float(r),asymptotic_p=float(p),exact_p=float(np.mean(np.abs(vals)>=abs(r)-1e-12)))

def group_test(ds):
    y=np.log([d['index'] for d in ds]); g=np.array([d['open'] for d in ds])
    model=ols(y,g); base=ols(y,np.empty((len(y),0)))
    observed=y[g==1].mean()-y[g==0].mean(); vals=[]
    for ids in itertools.combinations(range(len(y)),sum(g==0)):
        gg=np.ones(len(y),bool); gg[list(ids)]=False
        vals.append(y[gg].mean()-y[~gg].mean())
    model.update(effect_ratio=float(np.exp(observed)),
                 ratio_ci95=np.exp(model['ci95'][1]).tolist(),
                 exact_p=float(np.mean(np.abs(vals)>=abs(observed)-1e-12)),
                 lr_p=float(stats.chi2.sf(len(y)*np.log(base['rss']/model['rss']),1)),
                 base=base, names=[d['Sport / league']+' '+d['Sex'] for d in ds],
                 geometric_means=[float(np.exp(y[g==v].mean())) for v in [0,1]],
                 mannwhitney_asymptotic_p=float(stats.mannwhitneyu(y[g==0],y[g==1],method='asymptotic').pvalue))
    ranks=stats.rankdata(y); rank_obs=ranks[g==1].mean()-ranks[g==0].mean(); rank_vals=[]
    for ids in itertools.combinations(range(len(y)),sum(g==0)):
        gg=np.ones(len(y),bool); gg[list(ids)]=False
        rank_vals.append(ranks[gg].mean()-ranks[~gg].mean())
    model['rank_exact_p']=float(np.mean(np.abs(rank_vals)>=abs(rank_obs)-1e-12))
    return model

results={}
checks=[]
for d in rows:
    i=d['excel_row']
    for col,expected in [('K',d['margin']),('O',d['index'])]:
        value=cached['Data'][f'{col}{i}'].value
        assert (value is None and expected is None) or abs(value-expected)<1e-12
        checks.append(f'{col}{i}')
results['formula_cache_checks']={'checked':len(checks),'mismatches':0}
original=[d for d in rows if d['excel_row'] in range(2,10)]
results['original_margin_vs_inverse_N']=corr_exact([1/d['N'] for d in original],[d['margin'] for d in original])
results['original_margin_drop_volleyball']=corr_exact([1/d['N'] for d in original[:-1]],[d['margin'] for d in original[:-1]])
z=np.array([9.2,2.7,.9,-1.3,-7.8,-3,-4.6])
results['z_rounded']=corr_exact([1/d['N'] for d in original[:-1]],z)
results['original_index_vs_inverse_N']=corr_exact([1/d['N'] for d in original],[d['index'] for d in original])
results['individual_margin_four']=corr_exact([1/736,1/2400,1/450,1/1700],[.49,.50,.43,.14])
club=[d for d in rows if d['Level']=='Club' and d['index'] is not None]
strict=[d for d in club if not d['Overlap']]
initial=[dict(d,open=1) if d['excel_row']==3 else d for d in rows if d['excel_row'] in [3,4,5,6,7,8,9,11,12,13]]
results['league_system_initial_10']=group_test(initial)
results['league_system_strict_11']=group_test(strict)
results['league_system_all_club_15']=group_test(club)
results['league_system_strict_plus_cycling']=group_test(strict+[dict(rows[1],open=1)])
results['league_system_no_soccer_league_rows']=group_test([d for d in strict if d['Group']!='Soccer league'])
results['league_system_leave_one_out']=[dict(removed=d['Sport / league']+' '+d['Sex'],**group_test([x for x in strict if x is not d])) for d in strict]

y=np.log([d['index'] for d in strict]); g=np.array([d['open'] for d in strict]); f=np.array([d['female'] for d in strict])
results['system_sex_joint']=ols(y,np.column_stack([g,f]))
results['sex_only']=ols(y,f)
results['system_career_joint']=ols(y,np.column_stack([g,np.log([d['L'] for d in strict])]))
results['sex_sport_pairs']=[dict(sport='Basketball',male=11/6,female=4/3),dict(sport='Handball',male=8/3,female=8),dict(sport='Soccer',male=19/16,female=8)]
# Conditional permutations: keep female/male labels fixed and shuffle systems within sex.
obs=results['system_sex_joint']['beta'][1]; vals=[]
ixm=np.flatnonzero(f==0); ixf=np.flatnonzero(f==1)
for zm in itertools.combinations(ixm,sum(g[ixm]==0)):
    for zf in itertools.combinations(ixf,sum(g[ixf]==0)):
        gg=np.ones(len(y)); gg[list(zm)+list(zf)]=0
        vals.append(np.linalg.lstsq(np.column_stack([np.ones(len(y)),gg,f]),y,rcond=None)[0][1])
results['system_sex_joint']['sex_stratified_exact_p']=float(np.mean(np.abs(vals)>=abs(obs)-1e-12))

# Treat soccer as one sport family to expose dependence from multiple leagues.
families={'Basketball':[5,11],'Handball':[6,13],'Hockey':[7],'Water polo':[8],'Volleyball':[9],'Soccer':[12,15,17,18]}
frows=[]
for name,ids in families.items():
    ds=[d for d in strict if d['excel_row'] in ids]
    frows.append(dict(rows[0],**{'Sport / league':name,'Sex':'mixed','index':float(np.exp(np.mean(np.log([d['index'] for d in ds])))),'open':ds[0]['open']}))
results['system_sport_family_6']=group_test(frows)

# With/without tables from Markdown. Seasons/Games are treated as trials only for diagnostics.
withwithout=[('Patriots',6,20,0,46),('USA water polo',3,4,0,3),('Cuba volleyball',3,3,0,3),('Canada hockey',4,5,1,3),('Barcelona',14,17,10,22),('Hungary water polo',3,5,3,5),('USSR hockey',3,4,4,5)]
tests=[]
for name,a,n1,c,n0 in withwithout:
    record=dict(name=name,with_wins=a,with_trials=n1,without_wins=c,without_trials=n0)
    if name=='Barcelona':
        record.update(p=float(stats.binomtest(a,a+c,n1/(n1+n0)).pvalue),
                      test='conditional Poisson rate test',rate_with=a/n1,rate_without=c/n0)
    elif a<=n1 and c<=n0:
        record.update(fisher_p=float(stats.fisher_exact([[a,n1-a],[c,n0-c]]).pvalue),rate_with=a/n1,rate_without=c/n0)
        record['p']=record['fisher_p']; record['test']='Fisher exact'
    tests.append(record)
adj=holm([t['p'] for t in tests])
for t,p in zip(tests,adj): t['holm_p']=p
results['with_without']=tests
results['patriots_without_belichick_4years']=float(stats.fisher_exact([[6,14],[0,4]]).pvalue)
results['barcelona_poisson_count_rate_test']={
    'rate_ratio':(14/17)/(10/22),
    'conditional_binomial_p':float(stats.binomtest(14,24,17/39).pvalue),
    'note':'Poisson model permits >1 title/season; still assumes independent constant-rate periods.'}

# Ratios in paper: coordinates carry more precision than the printed table.
A=np.array([.0016891892,.0016863406,.0035087719,.0051813472,.0086956522])
B=np.array([.72962963,.72531034,.8,1.46212121,.59375])
baseline=np.array([.3,.3,.55,11/12,6/32])
results['cohort_ratio_effective']=corr_exact(A,B,rank=False)
results['cohort_ratio_baseline']=corr_exact(A,baseline,rank=False)
rr=results['cohort_ratio_effective']['r']; zz=np.arctanh(rr); zzse=1/np.sqrt(len(A)-3)
results['cohort_ratio_effective']['fisher_ci95']=np.tanh([zz-1.96*zzse,zz+1.96*zzse]).tolist()
results['cohort_ratio_no_NHL']=corr_exact(A[:4],B[:4],rank=False)
Ac=np.r_[A[:2].mean(),A[2:]]; Bc=np.r_[B[:2].mean(),B[2:]]
results['cohort_ratio_MLB_collapsed']=corr_exact(Ac,Bc,rank=False)

# Audit the four reported preparatory slopes using plotted intervals and cluster t df.
slopes=[1.97670864,-.34169931,7.37079516,2.23571416]
half=[1.66538403,6.85522131,13.01964095,2.60940796]
dfs=[29,19,11,31]; ps=[]
for b,h,df in zip(slopes,half,dfs):
    se=h/stats.t.ppf(.975,df); ps.append(float(2*stats.t.sf(abs(b/se),df)))
results['reported_output_reconstructed']={'p':ps,'holm':holm(ps),'raw_data_available':False}

# Independent primitive numeric columns only. Ratios would reuse title counts.
complete=[d for d in rows if d['Level']!='National' and all(d[x] is not None for x in ['H','J','T','L','N'])]
vars=['H','J','T','L','N']; data=np.log(np.array([[d[v] for v in vars] for d in complete],float))
rng=np.random.default_rng(20261003); pairtests=[]; reps=100000
ranks=np.column_stack([stats.rankdata(data[:,i]) for i in range(data.shape[1])]); ranks-=ranks.mean(axis=0); ranks/=np.linalg.norm(ranks,axis=0)
for i,j in itertools.combinations(range(len(vars)),2):
    r=float(ranks[:,i]@ranks[:,j]); null=np.empty(reps)
    for start in range(0,reps,10000):
        perms=rng.permuted(np.broadcast_to(ranks[:,j],(10000,len(complete))),axis=1)
        null[start:start+10000]=perms@ranks[:,i]
    p=(1+np.sum(abs(null)>=abs(r)-1e-12))/(reps+1)
    pairtests.append(dict(x=vars[i],y=vars[j],n=len(complete),rho=r,permutation_p=float(p)))
for t,p in zip(pairtests,holm([t['permutation_p'] for t in pairtests])):t['holm_p']=p
results['primitive_pairwise']=pairtests

Z=(data-data.mean(axis=0))/data.std(axis=0,ddof=1); R=Z.T@Z/(len(Z)-1)
ev,V=np.linalg.eigh(R); order=np.argsort(ev)[::-1]; ev=ev[order]; V=V[:,order]
parallel=np.empty((20000,len(vars)))
for i in range(len(parallel)):
    null=np.column_stack([rng.permutation(Z[:,j]) for j in range(Z.shape[1])])
    parallel[i]=np.linalg.eigvalsh(null.T@null/(len(Z)-1))[::-1]
results['pca']={'n':len(Z),'variables':vars,'names':[d['Sport / league'] for d in complete],
    'correlation_matrix':R.tolist(),'eigenvalues':ev.tolist(),'explained_fraction':(ev/ev.sum()).tolist(),
    'eigenvectors':V.tolist(),'parallel_95':np.quantile(parallel,.95,axis=0).tolist(),
    'parallel_p':((1+(parallel>=ev).sum(axis=0))/(len(parallel)+1)).tolist()}
def pca_sensitivity(ds, cols, draws=20000):
    xx=np.log(np.array([[d[c] for c in cols] for d in ds],float))
    xx=(xx-xx.mean(axis=0))/xx.std(axis=0,ddof=1)
    eig=np.linalg.eigvalsh(xx.T@xx/(len(xx)-1))[::-1]
    null=np.empty((draws,len(cols)))
    for ii in range(draws):
        zz=np.column_stack([rng.permutation(xx[:,j]) for j in range(xx.shape[1])])
        null[ii]=np.linalg.eigvalsh(zz.T@zz/(len(zz)-1))[::-1]
    eigenvalues,eigenvectors=np.linalg.eigh(xx.T@xx/(len(xx)-1))
    return dict(n=len(ds),vars=cols,eigenvalues=eig.tolist(),explained=(eig/eig.sum()).tolist(),eigenvectors=eigenvectors[:,::-1].tolist(),
                parallel_p=((1+(null>=eig).sum(axis=0))/(draws+1)).tolist())
results['pca_unique_Messi']=pca_sensitivity([d for d in complete if d['excel_row']!=4],vars)
results['pca_no_soccer_leagues']=pca_sensitivity([d for d in complete if d['Group']!='Soccer league'],vars)
results['pca_all_sexes_no_N']=pca_sensitivity([d for d in rows if d['Level']!='National' and all(d[v] is not None for v in ['H','J','T','L'])],['H','J','T','L'])
results['pca_all_sexes_no_N_unique_Messi']=pca_sensitivity([d for d in rows if d['Level']!='National' and d['excel_row']!=4 and all(d[v] is not None for v in ['H','J','T','L'])],['H','J','T','L'])
results['pca_all_sexes_no_N_no_soccer_leagues']=pca_sensitivity([d for d in rows if d['Level']!='National' and d['Group']!='Soccer league' and all(d[v] is not None for v in ['H','J','T','L'])],['H','J','T','L'])
results['pca_all_sexes_eigenvalue_holm']=holm(results['pca_all_sexes_no_N']['parallel_p'])
results['pca_eigenvalue_holm']=holm(results['pca']['parallel_p'])
results['primary_exploratory_axis_family']={
    'labels':['league system','sex','career length'],
    'p':[results['league_system_strict_11']['p'][1],results['sex_only']['p'][1],
         ols(y,np.log([d['L'] for d in strict]))['p'][1]]}
results['primary_exploratory_axis_family']['holm']=holm(results['primary_exploratory_axis_family']['p'])
results['ratio_coupling']={'index_margin_spearman':float(stats.spearmanr([d['index'] for d in complete],[d['margin'] for d in complete]).statistic),
    'identity':'log(index) + log(1+margin) = log(team_titles/best_other_titles)'}
# Targeted scope sensitivity; keep original inputs unchanged.
results['system_volleyball_historical_window_7']=group_test([dict(d,index=7) if d['excel_row']==9 else d for d in strict])
results['system_womens_handball_modern_7']=group_test([dict(d,index=7) if d['excel_row']==13 else d for d in strict])
results['input_rows']=rows
OUT.write_text(json.dumps(results,indent=2))
for k,v in results.items():
    if k in ['input_rows','league_system_leave_one_out']:continue
    print(k,json.dumps(v))
