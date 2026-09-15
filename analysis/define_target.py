"""Coordinate-derived 5XCO contact map; no model inference or affinity scoring."""
from pathlib import Path
import csv, hashlib, json
import gemmi
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'target'
block = gemmi.cif.read_file(str(OUT / '5xco.cif')).sole_block()
st = gemmi.make_structure_from_block(block)
# mmCIF has several author-chain A/B segments; select protein segments by residue content.
target = next(c for c in st[0] if c.name == 'A' and any(r.name == 'MET' and r.seqid.num == 1 for r in c))
peptide = next(c for c in st[0] if c.name == 'B' and any(r.name == 'ACE' for r in c))
residues = [r for r in target if 1 <= r.seqid.num <= 169]
assert [r.seqid.num for r in residues] == list(range(1, 170))
seq = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in residues)
wt = ''.join((OUT / 'P01116-2.fasta').read_text().splitlines()[1:])[:169]
diff = [(i+1, a, b) for i, (a, b) in enumerate(zip(wt, seq)) if a != b]
assert diff == [(12, 'G', 'D')], diff
assert seq[12] == 'G' and seq[60] == 'Q'
pepseq = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in peptide if 1 <= r.seqid.num <= 19)
assert pepseq == 'RRRRCPLYISYDPVCRRRR'
for name, header, sequence in [('target.fasta','KRAS_G12D_1-169|PDB=5XCO|auth_chain=A|GDP_state',seq),
                               ('target_wt.fasta','KRAS4B_WT_1-169|UniProt=P01116-2',wt)]:
    (ROOT/name).write_text(f'>{header}\n{sequence}\n')
def atoms(res):
    # Use primary/blank conformer, non-hydrogen atoms of nonzero occupancy.
    return [a for a in res if not a.element.is_hydrogen and a.occ > 0 and a.altloc in ('\x00', 'A')]
pairs = []
for r in residues:
    for p in peptide:
        ra, pa = atoms(r), atoms(p)
        if not ra or not pa: continue
        d = np.array([[a.pos.dist(b.pos) for b in pa] for a in ra])
        i, j = np.unravel_index(d.argmin(), d.shape)
        if d[i,j] <= 5.0:
            pairs.append({'target_residue': r.seqid.num, 'target_name': r.name, 'peptide_residue': p.seqid.num,
                          'peptide_name': p.name, 'target_atom': ra[i].name, 'peptide_atom': pa[j].name,
                          'min_distance_A': round(float(d[i,j]), 4), 'within_4A': bool(d[i,j] <= 4)})
with (OUT/'contacts.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
contact4=sorted({x['target_residue'] for x in pairs if x['within_4A']})
contact5=sorted({x['target_residue'] for x in pairs})
# Preserve original nucleotide and chemically complete peptide; remove waters/EDO/tag.
clean=st.clone()
for model in clean:
    for chain in model:
        for k in range(len(chain)-1,-1,-1):
            r=chain[k]
            keep=(chain.name=='A' and ((r.het_flag=='A' and 1<=r.seqid.num<=169) or r.name=='GDP')) or (chain.name=='B' and r.name!='HOH')
            if not keep: del chain[k]
clean.merge_chain_parts()
# Cropping coordinates alone does not crop entity sequence/label numbering.
# Remove the GS expression tag from entity metadata and normalize label_seq_id.
for entity in clean.entities:
    if entity.name == '1': entity.full_sequence = [r.name for r in residues]
for chain in clean[0]:
    if chain.name == 'A':
        for residue in chain:
            if residue.het_flag == 'A': residue.label_seq = residue.seqid.num
clean.make_mmcif_document().write_file(str(OUT/'5xco-reference.cif'))
clean.write_pdb(str(OUT/'5xco-reference.pdb'))
design_target=clean.clone()
for i in range(len(design_target[0])-1,-1,-1):
    if design_target[0][i].name=='B': del design_target[0][i]
design_target.connections.clear()
for i in range(len(design_target.entities)-1,-1,-1):
    if design_target.entities[i].name not in ('1','3'): del design_target.entities[i]
design_target.make_mmcif_document().write_file(str(OUT/'kras-g12d-gdp.cif'))
manifest={'pdb':'5XCO','resolution_A':st.resolution,'construct':'KRAS1-169','state':'GDP',
 'mutations_vs_uniprot_P01116_2':diff,'target_isoform':'KRAS4B P01116-2','target_chain':'A','peptide_chain':'B','target_length':len(seq),
 'positive_control_sequence':pepseq,'positive_control_length':len(pepseq),'disulfide_peptide_positions':[5,15],
 'termini':['ACE B:0','NH2 B:20'],'contacts_heavy_atom_4A':contact4,'contacts_heavy_atom_5A':contact5,
 'method':'asymmetric unit, target1-169 vs peptide B0-20 including caps; non-H, occupancy>0, altloc blank/A; no waters or crystal mates',
 'uniprot_mapping':{'P01116':'KRAS','P01111':'NRAS','P01112':'HRAS'}}
(OUT/'target-qc.json').write_text(json.dumps(manifest,indent=2)+'\n')
rows=[]
for i in contact5:
    items=[x for x in pairs if x['target_residue']==i]
    rows.append(f"| {seq[i-1]}{i} | {min(x['min_distance_A'] for x in items):.3f} | {'yes' if i in contact4 else 'no'} | "+', '.join(str(x['peptide_residue']) for x in items)+' |')
(ROOT/'POCKET.md').write_text('''# KRAS G12D target and observed pocket

The 1–169 construct matches author chain A of [PDB 5XCO](https://www.rcsb.org/structure/5XCO), a 1.25 Å GDP-state crystal complex. All 169 residues have coordinates. Relative to [UniProt P01116-2 (KRAS4B)](https://www.uniprot.org/uniprotkb/P01116/entry), the sole difference in this interval is G12D. Residues 13 and 61 are G and Q. The deposited expression sequence also contains an N-terminal GS tag; observed Ser0 is excluded from the target. GDP is retained in the reference coordinate file. A FASTA alone does not encode nucleotide state.

Isoform QC caught a real mismatch: the displayed P01116 sequence is KRAS4A and differs from 5XCO at 151,153,165,166,167,168 in addition to G12D. Both the mutant and WT counter-screen therefore use KRAS4B. The first failed comparison and corrected rerun are preserved in the logs; no target was silently substituted.

Accession correction: P01116 = KRAS, P01111 = NRAS, P01112 = HRAS. The original requested HRAS/NRAS ordering was reversed.

Contacts below are recalculated from the asymmetric unit, using minimum non-hydrogen atom distance from target A1–169 to peptide B0–20, including acetyl and amide caps. Alternate conformer A/blank and positive occupancy only; waters and symmetry mates are excluded. The 4 Å set is a geometric pocket definition, not an energy or binding-affinity calculation. The 5 Å shell is reported for cutoff sensitivity. Water-mediated interactions described in the paper need not occur in the 4 Å direct-contact set.

| Target residue | Minimum distance (Å) | Within 4 Å | Peptide author positions within 5 Å |
|---|---:|:---:|---|
'''+ '\n'.join(rows)+'''

The reference inhibitor is full-length KRpep-2d, 19 residues with a Cys5–Cys15 disulfide and acetylated/amidated termini. Position 12 in the peptide is Asp; it must not be confused with KRAS Asp12. Native 5XCO is the experimental reference, not a predicted design. Atom-pair distances are in `results/target/contacts.csv`; target checks and contact definitions are in `target-qc.json`.

Reference: Sogabe et al., PMID 28740607, DOI [10.1021/acsmedchemlett.7b00128](https://doi.org/10.1021/acsmedchemlett.7b00128). Source URLs, timestamps and SHA-256 hashes: `results/target/source-receipts.json`.
''')
print(json.dumps(manifest,indent=2))
