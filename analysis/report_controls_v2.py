"""Render revision-2 recorded-data diagnostics, without changing any gate."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='KRpep-Zero'

R=Path(__file__).resolve().parents[1]
run=R/'results/control-remediation-v2-002'
g=json.loads((run/'analysis/gate-summary.json').read_text())
rows=list(csv.DictReader((run/'analysis/per-seed.csv').open()))
audit=json.loads((run/'analysis/structure-audit.json').read_text())
metadata=json.loads((run/'extracted/metadata.json').read_text())
pos=[r for r in rows if r['control_id']=='KRpep-2d']
neg=[r for r in rows if r['control_id']!='KRpep-2d']
pink,teal,gold,red='#ed5aa9','#65e5c3','#f0c86a','#ff776b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':'#e7efef',
 'axes.labelcolor':'#b7cbd5','xtick.color':'#b7cbd5','ytick.color':'#b7cbd5',
 'axes.edgecolor':'#365063','axes.facecolor':'#101f2c','figure.facecolor':'#09131c',
 'savefig.facecolor':'#09131c','axes.titleweight':'bold'})
fig,axs=plt.subplots(2,2,figsize=(16,12),dpi=100)
fig.subplots_adjust(left=.08,right=.96,bottom=.12,top=.82,hspace=.53,wspace=.3)
title='The repair passes both control gates.' if g['passed'] else 'The repair does not clear validation.'
fig.text(.08,.955,title,fontsize=27,weight='bold')
fig.text(.08,.91,'REVISION 2  /  COMPLETE MOLECULAR GRAPHS  /  ALL SIX SEEDS',fontsize=11,color=teal)
fig.text(.08,.864,f"Separation: {'PASS' if g['separation_passed'] else 'FAIL'}    ·    Chemistry: {'PASS' if g['chemistry_passed'] else 'FAIL'}    ·    Mean gap {g['positive_minus_scramble']:+.4f}",fontsize=14,color=gold)
ax=axs[0,0]
for p,n in zip(pos,neg):
    values=[float(p['pair_iptm_mean']),float(n['pair_iptm_mean'])]
    ax.plot([0,1],values,color='#6a8090',alpha=.65,lw=1)
    ax.scatter([0,1],values,c=[pink,teal],s=65,zorder=3)
    offsets={('17',0):2,('42',0):-12,('101',0):8,('17',1):8,('42',1):2,('101',1):-12}
    for x,y in enumerate(values):ax.annotate(p['seed'],(x,y),xytext=(8,offsets[(p['seed'],x)]),textcoords='offset points',fontsize=9)
for x,key,color in [(0,'positive_mean_pair_iptm',pink),(1,'scramble_mean_pair_iptm',teal)]:
    ax.plot([x-.13,x+.13],[g[key],g[key]],color=color,lw=4)
ax.set(xlim=(-.3,1.4),ylim=(0,1.04),xticks=[0,1],xticklabels=['KRpep-2d','Proposed scramble'],ylabel='Target–peptide pair ipTM')
ax.set_title('A  /  Within-revision confidence',loc='left',pad=15)
ax.text(0,-.22,'Dots: all seeds · bars: means · lines: paired seeds.\nFull 0–1 scale; confidence is not binding affinity.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
ax=axs[0,1]
deltas=list(g['paired_seed_differences'].values())+[g['positive_minus_scramble']]
ax.axvline(0,color='#698293',lw=1);ax.axvline(.15,color=gold,ls='--',lw=1.5,label='Required mean gap +0.150')
for i,d in enumerate(deltas):
    color=gold if i==3 else teal
    ax.plot([0,d],[i,i],color=color,lw=3)
    ax.scatter([d],[i],c=color,s=75,marker='D' if i==3 else 'o')
    ax.annotate(f'{d:+.4f}',(d,i),xytext=(5,10),textcoords='offset points',fontsize=9)
lo=min(-.04,min(deltas)-.08);hi=max(.22,max(deltas)+.14)
ax.set(xlim=(lo,hi),ylim=(3.7,-.7),yticks=range(4),yticklabels=['Seed 17','Seed 42','Seed 101','Mean'],xlabel='Positive − proposed scramble')
ax.set_title('B  /  The unchanged separation rule',loc='left',pad=15)
ax.legend(frameon=False,fontsize=9,loc='lower right',labelcolor=gold)
ax=axs[1,0]
matrix=[];labels=[]
for a in audit:
    geometry=a['geometry']
    matrix.append([int(v['passed']) for v in geometry['critical_links']]+[int(geometry['stereochemistry_passed'])])
    labels.append(('Positive' if a['id']=='KRpep-2d' else 'Scramble')+' / '+str(a['seed']))
from matplotlib.colors import ListedColormap
ax.imshow(matrix,cmap=ListedColormap([red,teal]),vmin=0,vmax=1,aspect='auto',alpha=.7)
for i,line in enumerate(matrix):
    for j,passed in enumerate(line):ax.text(j,i,'PASS' if passed else 'FAIL',ha='center',va='center',fontsize=9,color='#09131c',weight='bold')
ax.set(xticks=range(4),xticklabels=['Acetyl\nC–N','Disulfide\nS–S','Amide\nC–N','All 20\ncenters'],yticks=range(6),yticklabels=labels)
ax.set_title('C  /  Chemistry must survive prediction',loc='left',pad=15)
ax.text(0,-.25,'Critical links: preregistered RDKit bounds ±12.5%.\nCenters: coordinate-assigned stereochemistry matches the input.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
ax=axs[1,1]
values=[float(r['positive_core_CA_RMSD_A']) for r in pos]
ax.bar(range(3),values,color=pink,width=.5)
upper=max(2,max(values)*1.23)
for i,v in enumerate(values):ax.text(i,v+upper*.035,f'{v:.2f} Å',ha='center',fontsize=11)
ax.set(xticks=range(3),xticklabels=['Seed 17','Seed 42','Seed 101'],ylabel='Mapped core Cα RMSD (Å)',ylim=(0,upper))
ax.set_title('D  /  Positive-control pose diagnostic',loc='left',pad=15)
ax.text(0,-.25,'Target A1–169 Cα fit; mapped peptide Cα5–15 (11 atoms).\nEvery seed shown; reference coordinates were not model inputs.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
for ax in axs.flat:
    ax.spines[['top','right']].set_visible(False)
    if ax is not axs[1,0]:ax.grid(axis='y',color='#263b49',alpha=.5);ax.set_axisbelow(True)
fig.text(.08,.022,'Do not compare absolute confidence across revisions: peptide tokenization changed. The scramble is an unvalidated negative proposal.',fontsize=10,color='#a2b8c5')
for suffix in ('png','svg'):fig.savefig(R/f'results/figures/control-remediation-v2.{suffix}',dpi=100,metadata={'Date':None} if suffix=='svg' else None)
plt.close(fig)

lines=['# Full-molecule control remediation — revision 2','',title,'',
 f"**Decision: `{g['decision']}`.** All six preregistered predictions completed; separation {'passed' if g['separation_passed'] else 'failed'} and chemistry {'passed' if g['chemistry_passed'] else 'failed'}.",'',
 'The original revision-1 failure is preserved. This additional experiment changed the representation of the same positive control and proposed scramble to complete chemical graphs. It did not change their sequences, seeds or the confidence-separation rule.','',
 '## Frozen gates','',
 f"- Mean positive pair ipTM: {g['positive_mean_pair_iptm']:.6f}; proposed scramble: {g['scramble_mean_pair_iptm']:.6f}.",
 f"- Difference: {g['positive_minus_scramble']:+.6f}; required ≥ +0.150. Positive higher on {g['positive_higher_seed_count']}/3 paired seeds; required ≥2/3.",
 '- Chemistry requires all three diagnosed critical links within the precomputed RDKit distance bounds expanded by 12.5%, and all 20 stereocenters matching the input in every seed. The fraction of all 183 peptide bonds within bounds is reported separately.','',
 '## Every seed','',
 '| Control | Seed | A→B ipTM | B→A ipTM | Mean | Mapped interface pLDDT | Bonds in bounds | Centers correct | Critical links | Core RMSD Å |',
 '|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
for r,a in zip(rows,audit):
    assert (r['control_id'],int(r['seed']))==(a['id'],a['seed'])
    geo=a['geometry'];centers=sum(c['passed'] for c in geo['stereocenters'])
    plddt=f"{float(r['mapped_CA_interface_plddt']):.2f}" if r['mapped_CA_interface_plddt'] else 'No contact'
    rmsd=f"{float(r['positive_core_CA_RMSD_A']):.3f}" if r['positive_core_CA_RMSD_A'] else '—'
    lines.append(f"| {r['control_id']} | {r['seed']} | {float(r['pair_iptm_0_1']):.4f} | {float(r['pair_iptm_1_0']):.4f} | {float(r['pair_iptm_mean']):.4f} | {plddt} | {geo['bonds_within_expanded_bounds']}/183 | {centers}/20 | {'PASS' if geo['critical_links_passed'] else 'FAIL'} | {rmsd} |")
lines += ['', '## Interpretation and limits','',
 'Interface confidence is not affinity, cellular activity or biological selectivity. The proposed scramble is not an experimentally established nonbinder. A failed separation gate does not establish that either molecule binds or fails to bind.', '',
 'Absolute confidence and pLDDT must not be pooled or compared with revision 1: atom-token representation changes the model inputs and normalization. Pose RMSD uses the exact positive-control correspondence after fitting only target Cα1–169; no peptide refitting or best-seed selection is used.', '',
 'The input formal charge follows the pinned CCD representation (+8, neutral Asp acid). This is not a physiological protonation assignment. Possible training-set overlap with 5XCO also limits prospective interpretation.','',
 '## Reproducibility and resources','',
 f"Pinned code `{metadata['code_revision']}`; weights `{metadata['weights_revision']}`. One L4; recorded remote function elapsed {metadata['elapsed_seconds']:.1f} seconds. Elapsed time is not an invoice or a verified remaining-credit balance.", '',
 'Six revision-2 runs plus six revision-1 runs consume 12 validation units. The declared maximum of 49 candidate triplets and 10 WT triplets would total 189 units only if both gates pass. No affinity inference was requested.','',
 'The archived protocol, preprocessing hashes, input graphs, all structures, per-seed table and complete bond/stereochemistry audit are retained in `results/control-remediation-v2-002/`. Rebuild with `analysis/analyze_controls_v2.py`, then `analysis/report_controls_v2.py`.','']
(R/'results/REMEDIATION_V2_REPORT.md').write_text('\n'.join(lines))
print(title)
