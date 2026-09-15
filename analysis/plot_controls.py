"""Plot every control seed and the frozen gate from recorded measurements."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='KRpep-Zero'
import gemmi

R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'results/controls/per-seed.csv').open()))
gate=json.loads((R/'results/controls/gate-summary.json').read_text())
pos=[r for r in rows if r['control_id']=='KRpep-2d']; neg=[r for r in rows if r['control_id']!='KRpep-2d']
pink,teal,gold,red='#ed5aa9','#65e5c3','#f0c86a','#ff776b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':'#e7efef','axes.labelcolor':'#b7cbd5',
 'xtick.color':'#b7cbd5','ytick.color':'#b7cbd5','axes.edgecolor':'#365063','axes.facecolor':'#101f2c',
 'figure.facecolor':'#09131c','savefig.facecolor':'#09131c','axes.titleweight':'bold'})
fig,axs=plt.subplots(2,2,figsize=(16,12),dpi=100)
fig.subplots_adjust(left=.075,right=.96,bottom=.11,top=.83,hspace=.48,wspace=.27)
fig.text(.075,.95,'The controls do not separate.',fontsize=29,weight='bold')
fig.text(.075,.907,'CONTROL CALIBRATION  /  6 PREDICTIONS  /  SEEDS 17 · 42 · 101',fontsize=11,color=teal)
fig.text(.075,.867,f'Mean gap {gate["positive_minus_scramble"]:+.4f}; required ≥ +0.150.  Further screening stopped.',fontsize=14,color=gold)
ax=axs[0,0]
for i,(p,n) in enumerate(zip(pos,neg)):
    vals=[float(p['pair_iptm_mean']),float(n['pair_iptm_mean'])]
    ax.plot([0,1],vals,color='#6a8090',alpha=.65,lw=1)
    ax.scatter([0,1],vals,c=[pink,teal],s=70,zorder=3)
    for x,y in enumerate(vals):ax.annotate(p['seed'],(x,y),xytext=(8,2),textcoords='offset points',fontsize=9)
for x,name,color in [(0,'positive_mean_pair_iptm',pink),(1,'scramble_mean_pair_iptm',teal)]:
    y=gate[name];ax.plot([x-.15,x+.15],[y,y],color=color,lw=4)
ax.set(xlim=(-.4,1.5),ylim=(.86,.975),xticks=[0,1],xticklabels=['KRpep-2d','Proposed scramble'],ylabel='Target–peptide pair ipTM')
ax.set_title('A  /  Confidence overlaps',loc='left',pad=15)
ax.text(0,-.20,'Dots: all seeds · bars: means · lines: paired seeds\nZoomed y-axis; confidence is not binding affinity.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
ax=axs[0,1]
delta=np.array([float(p['pair_iptm_mean'])-float(n['pair_iptm_mean']) for p,n in zip(pos,neg)])
ax.axvline(0,color='#698293',lw=1);ax.axvline(.15,color=gold,ls='--',lw=1.5)
for i,d in enumerate(delta):
    ax.plot([0,d],[i,i],color=teal,lw=3);ax.scatter([d],[i],c=teal,s=55)
    ax.annotate(f'{d:+.4f}',(d,i),xytext=(8,10),textcoords='offset points',va='bottom',fontsize=10)
ax.scatter([gate['positive_minus_scramble']],[3],c=red,s=90,marker='D')
ax.set(xlim=(-.045,.175),ylim=(3.6,-.6),yticks=[0,1,2,3],yticklabels=['Seed 17','Seed 42','Seed 101','Mean'],xlabel='Positive − proposed scramble')
ax.set_title('B  /  Predeclared gate fails',loc='left',pad=15)
ax.text(.15,3.5,'Required\nmean gap',ha='center',va='bottom',fontsize=9,color=gold)
ax=axs[1,0]
values=[float(r['positive_core_CA_5_to_15_RMSD_A']) for r in pos]
bars=ax.bar(range(3),values,color=[pink,red,pink],width=.5)
for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v+.6,f'{v:.2f} Å',ha='center',fontsize=11)
ax.set(xticks=range(3),xticklabels=['Seed 17','Seed 42','Seed 101'],ylabel='Mapped core Cα RMSD (Å)',ylim=(0,26))
ax.set_title('C  /  Positive-control pose is seed-sensitive',loc='left',pad=15)
ax.text(0,-.20,'Target A1–169 Cα superposition; peptide B5–15 Cα (11 atoms).\nSame sequence correspondence; no peptide refitting.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
ax=axs[1,1]
for i,(p,n) in enumerate(zip(pos,neg)):
    ax.scatter([i-.08,i+.08],[float(p['peptide19_C_NH2_N_A']),float(n['peptide19_C_NH2_N_A'])],c=[pink,teal],s=70)
ref=gemmi.read_structure(str(R/'results/target/5xco-reference.cif'))[0]['B']
def at(num,name):return next(a for r in ref if r.seqid.num==num for a in r if a.name==name and a.altloc in ('\x00','A'))
native=at(19,'C').pos.dist(at(20,'N').pos)
ax.axhline(native,color=gold,ls='--',label=f'5XCO: {native:.3f} Å')
ax.legend(frameon=False,labelcolor=gold,loc='upper left',fontsize=10)
ax.set(xticks=range(3),xticklabels=['Seed 17','Seed 42','Seed 101'],ylabel='Terminal C–N distance (Å)',ylim=(.5,1.6))
ax.set_title('D  /  Cap geometry needs repair',loc='left',pad=15)
ax.text(0,-.20,'Peptide B19 C → amidating NH₂ N; all six predictions.\nParser acceptance did not ensure realistic output geometry.',transform=ax.transAxes,fontsize=9,color='#a2b8c5')
for ax in axs.flat:
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#263b49',alpha=.5);ax.set_axisbelow(True)
fig.text(.075,.035,'Boltz 2.2.1 · pinned weights · identical inputs/settings except peptide sequence and seed · no affinity inference',fontsize=10,color='#a2b8c5')
for suffix in ('png','svg'):fig.savefig(R/f'results/figures/control-calibration.{suffix}',dpi=100,metadata={'Date':None} if suffix=='svg' else None)
plt.close(fig)
print('Saved six-seed control figure (1600 × 1200 PNG and SVG).')
