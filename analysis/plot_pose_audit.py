"""All-seed native-contact and displacement diagnostics; no selection gate."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parents[1]
rows=[r for r in csv.DictReader((R/'results/pose-audit/pose-audit.csv').open()) if r['positive_id']=='KRpep-2d']
plt.rcParams.update({'svg.hashsalt':'KRpep-Zero','font.family':'DejaVu Sans','font.size':12})
fig,axs=plt.subplots(1,2,figsize=(13,5.5),layout='constrained')
colors=['#db4184','#008b80'];x=np.arange(3)
for i,v in enumerate(['v1','v2']):
 rr=[r for r in rows if r['version']==v]
 y=[float(r['native_contact_recovery_fraction'])*100 for r in rr]
 bars=axs[0].bar(x+(i-.5)*.32,y,.30,color=colors[i],label=v)
 for b,r in zip(bars,rr):axs[0].text(b.get_x()+b.get_width()/2,b.get_height()+2,f"{r['native_contact_recovered']}/41",ha='center',fontsize=10)
 y=[float(r['target_fitted_core5_15_CA_RMSD_A']) for r in rr]
 bars=axs[1].bar(x+(i-.5)*.32,y,.30,color=colors[i],label=v)
 for b,val in zip(bars,y):axs[1].text(b.get_x()+b.get_width()/2,val+.5,f'{val:.2f}',ha='center',fontsize=10)
for ax in axs:
 ax.set_xticks(x,['Seed 17','Seed 42','Seed 101']);ax.spines[['top','right']].set_visible(False)
 ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axs[0].set(ylabel='Experimental residue contacts recovered (%)',ylim=(0,110),title='A  |  Positive-control native contacts')
axs[1].set(ylabel='Target-fitted peptide core Cα RMSD (Å)',ylim=(0,26),title='B  |  Positive-control pose displacement')
axs[0].legend(frameon=False)
fig.suptitle('Geometry repair did not ensure experimental-pose recovery',fontsize=17,fontweight='bold')
for ext in ['png','svg']:fig.savefig(R/f'results/figures/positive-pose-audit.{ext}',dpi=160,metadata={'Date':None} if ext=='svg' else None)
