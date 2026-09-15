"""Build study PDFs from recorded results and the audited evidence matrix."""
from pathlib import Path
import csv,json
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether

R=Path(__file__).resolve().parents[1];OUT=R/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
v1=json.loads((R/'results/controls/gate-summary.json').read_text())
v2=json.loads((R/'results/control-remediation-v2-002/analysis/gate-summary.json').read_text())
rows=list(csv.DictReader((R/'results/control-remediation-v2-002/analysis/per-seed.csv').open()))
controls=list(csv.DictReader((R/'results/study-package/experimental-control-candidates.csv').open()))
audit=json.loads((R/'results/control-remediation-v2-002/analysis/structure-audit.json').read_text())
protenix_summary_path=R/'results/study-package/protenix-diagnostic-summary.json'
protenix_summary=json.loads(protenix_summary_path.read_text()) if protenix_summary_path.exists() else {'attempts':[]}
assert len(rows)==6 and all(a['geometry']['bonds_within_expanded_bounds']==183 for a in audit)
assert v2['chemistry_passed'] and not v2['passed']
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=colors.HexColor('#102A43'),spaceAfter=13))
styles.add(ParagraphStyle(name='Deck',fontName='Helvetica',fontSize=12,leading=17,textColor=colors.HexColor('#334e68'),spaceAfter=13))
styles.add(ParagraphStyle(name='Copy',fontName='Helvetica',fontSize=10.2,leading=14.4,spaceAfter=9,textColor=colors.HexColor('#172b3a')))
styles.add(ParagraphStyle(name='Section',fontName='Helvetica-Bold',fontSize=14,leading=18,spaceBefore=10,spaceAfter=9,textColor=colors.HexColor('#102A43')))
styles.add(ParagraphStyle(name='Fine',fontName='Helvetica',fontSize=8.1,leading=11.2,spaceAfter=7,textColor=colors.HexColor('#486581')))
styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=9,leading=12,textColor=colors.HexColor('#172b3a')))
styles.add(ParagraphStyle(name='CellHead',fontName='Helvetica-Bold',fontSize=9,leading=12,textColor=colors.white))
W=A4[0]-100
def p(text,style='Copy'):return Paragraph(text,styles[style])
def title(text):return p(text,'ReportTitle')
def h(text):return p(text,'Section')
def table(data,widths):
    cells=[[p(escape(str(x)),'CellHead' if i==0 else 'Cell') for x in row] for i,row in enumerate(data)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#102A43')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d5dee6')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f6f9')])]))
    return t
def fig(name):return Image(str(R/'results/figures'/name),width=W,height=W*.75)
def maybe_fig(name,height_ratio=.46):
    path=R/'results/figures'/name
    return [Image(str(path),width=W,height=W*height_ratio)] if path.exists() else []
def friendly_status(status):
    return {
        'failed_before_prediction':'failed before prediction',
        'failed_with_partial_outputs':'failed with partial outputs',
        'returned_without_expected_outputs':'returned without expected outputs',
        'pending_or_unreturned':'not returned',
        'completed':'completed',
        'missing':'not returned',
    }.get(status,status)
def protenix_rows():
    data=[['Attempt','Status','Output','Reviewer note']]
    for item in protenix_summary.get('attempts',[]):
        status=friendly_status(item.get('status','unknown'))
        model=item.get('model') or 'not returned'
        output=f"{item.get('prediction_cif_count',0)} CIFs"
        if item.get('positive_core_rmsd_A'):
            rmsd=', '.join(f"{float(v):.2f}" for v in item['positive_core_rmsd_A'])
            chemistry='chemistry checks failed' if (item.get('all_bonds_in_bounds') is False or item.get('all_stereocenters_correct') is False) else 'chemistry checks passed'
            output=f"{output}; positive contacts 0/41 each seed (17, 42, 101); scramble NA; RMSD {rmsd} A; {chemistry}"
        note=('Checkpoint HTTP 403 before prediction' if item.get('label') == 'Protenix-v2' else (item.get('error') or 'Descriptive diagnostic only; no candidate gate change'))
        data.append([item.get('label',model),status,output,note])
    if len(data)==1:
        data.append(['Protenix diagnostic','not returned','0 CIFs','No local receipt available'])
    return data
def footer(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#486581'))
    canvas.drawString(50,28,'KRpep-Zero  |  Research review  |  15 September 2026')
    canvas.drawRightString(A4[0]-50,28,str(doc.page))
def build(name,story):
    doc=SimpleDocTemplate(str(OUT/name),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=43,bottomMargin=48,title='KRpep-Zero chemistry and control validation',author='KRpep-Zero',pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

story=[title('KRpep-Zero'),p('Chemistry and control validation for KRAS peptide modeling','Deck'),
 p('<b>Conclusion.</b> Encoding each complete capped peptide as one molecular graph passed the declared Boltz chemistry checks. The positive control did not separate sufficiently from the proposed scramble, and its predicted poses did not consistently recover the experimental binding mode. The independent Protenix diagnostic positive control recovered 0/41 native contacts in each seed (seeds 17, 42 and 101); scramble contact recovery is NA, and chemistry checks failed. These results do not justify selecting novel peptide binders.'),
 h('Purpose of this study'),p('The intended campaign targeted the Switch-II-adjacent pocket of KRAS G12D with cyclic peptides. We tested the computational workflow against the crystallographic KRpep-2d reference before committing to a large candidate screen. Two model-input representations and all three preregistered random seeds are retained.'),
 table([['Recorded work','Result'],['Target and reference','KRAS4B G12D residues 1-169, GDP, PDB 5XCO'],['Sequence-model calculation','ESMC-300M masked profiles for matched WT and G12D targets'],['Model controls','18 predictions total: 12 Boltz + 6 Protenix, covering 2 control identities'],['Generator technical pilot','2 structures generated; 0 passed built-in filters'],['Main discovery screen','Not run after failed control gates'],['Experimental activity','No new binding, cellular or in vivo experiment']], [W*.36,W*.64]),
 h('What the project contributes'),p('The reproducible record links exact chemical inputs to model outputs and exposes a gap between parser acceptance, chemically credible coordinates and useful selection confidence. The representation repair improves the measured geometry checks in this case. It does not establish a general-purpose peptide-docking remedy.'),
 p('This work is a computational validation study with a negative selection result. The original novel-binder objective remains unmet. The evidence and limitations are presented for scientific review.','Fine'),PageBreak(),
 title('Experimental reference and methods'),
 h('Reference identity'),p('PDB 5XCO contains GDP-bound KRAS G12D and the 19-residue inhibitor Ac-RRRRCPLYISYDPVCRRRR-NH2. The peptide has an N-acetyl group, C-terminal amide and Cys5-Cys15 disulfide. The modeled KRAS4B construct spans residues 1-169; the matched WT target differs only at position 12. The original displayed UniProt KRAS4A sequence would have introduced additional isoform differences. [1]'),
 h('Published binding measurements'),p('In the crystallographic paper, KRpep-2d has SPR KD values of 8.9 nM for GDP-loaded G12D and 58 nM for GDP-loaded WT. Their ratio is 6.52. The separately reported exchange-inhibition IC50 is 1.6 nM. These are published measurements from distinct assays, not model predictions or measurements performed here. [1]'),
 h('Two representations and fixed sampling'),p('Both revisions used official Boltz 2.2.1, pinned code and weights, the same target/GDP, the same control sequences, seeds 17, 42 and 101, three recycles and 200 sampling steps. Each control/seed produced one prediction. The proposed scramble was RRRRCILVPSYYPDCRRRR with the same caps and disulfide. No peptide affinity inference was requested.'),
 p('Revision 1 represented the peptide as a protein chain with separate terminal cap components. Revision 2 represented the complete peptide as one connected molecular graph containing 179 heavy atoms. It preserved 20 stereocenters and used fixed preprocessing artifacts across seeds. The +8 formal-charge convention follows the pinned component dictionary, not a physiological-pH prediction.'),
 h('Declared decisions and independent interpretation'),p('Within each revision, the mean positive-minus-scramble pair-ipTM gap had to be at least +0.150, with the positive higher on at least two of three paired seeds. Revision 2 additionally required all three diagnosed covalent links and all 20 stereocenters to pass in every output. Thresholds were recorded before the corresponding neural outputs. Absolute confidence must not be compared across revisions because peptide tokenization changed.'),
 p('The 18 predictions are stochastic model runs of two control identities, not 18 independent biological observations or biological replicates. The proposed scramble lacks an experimentally established inactive label. Neither the chosen confidence gate nor its failure establishes binding affinity.','Fine'),PageBreak(),
 title('Revision 1 exposed a validation failure'),fig('control-calibration.png'),
 p(f"Positive mean pair ipTM was {v1['positive_mean_pair_iptm']:.4f}, versus {v1['scramble_mean_pair_iptm']:.4f} for the proposed scramble. The gap {v1['positive_minus_scramble']:+.4f} failed the required +0.150. Two of three paired seeds favored the positive, which did not satisfy both criteria."),
 p('The highest-confidence positive pose was displaced from the experimental peptide binding site. Additional coordinate diagnostics found compressed terminal-cap bonds. A source/input audit showed that the separate cap links lacked the two-sided distance guidance used for ordinary molecular bonds. This identifies a coverage gap; it does not prove the cause of the confidence overlap.'),
 p('All seeds remain visible. Core RMSD fits target C-alpha residues 1-169, then evaluates the exactly corresponding positive-peptide C-alpha residues 5-15 without refitting the peptide. The geometry observations did not replace the original failed gate.','Fine'),PageBreak(),
 title('Revision 2 repaired geometry but failed selection'),fig('control-remediation-v2.png'),
 p(f"All six outputs preserved all 183 molecular bonds within the declared expanded bounds and all 20 input stereocenters. The confidence gap was {v2['positive_minus_scramble']:+.4f}, below +0.150. Positive-control core RMSDs were 21.40, 12.24 and 11.03 angstrom for seeds 17, 42 and 101."),
 p('Passing these coordinate checks does not establish correct peptide energetics or target engagement. The full-graph representation changed the model input and confidence normalization; lower or higher absolute confidence relative to revision 1 is not evidence of improved or worsened binding.'),
 p('Both protocols remain failed for candidate advancement. The main 60-design screen, WT candidate counter-screen, developability ranking and top-three assay draft have no justified selected designs to act on.','Fine'),PageBreak(),
 title('Independent native-contact audit'),
 Image(str(R/'results/figures/positive-pose-audit.png'),width=W,height=W*5.5/13),
 p('The experimental reference has 41 target-peptide residue pairs with at least one heavy-atom distance at or below 5 angstrom. Revision 1 recovered 35, 0 and 37 of these pairs; revision 2 recovered 1, 4 and 12. This calculation uses all three seeds and exact positive-peptide residue correspondence.'),
 h('What these diagnostics establish'),p('Two revision 1 seeds approach the reference pose while the third is displaced. All three revision 2 poses recover fewer than one third of the native contacts. The independent contact metric therefore supports the RMSD finding: passing the declared chemistry checks did not ensure reference-pose recovery.'),
 h('Geometry and mapping checks'),p('Each full-graph atom map was checked against the actual per-run processed molecule atom index, element and name. Target residues 1-169 were sequence-verified. Across all 12 Boltz control outputs, no target-peptide heavy-atom pair was closer than 2 angstrom. This is a simple distance diagnostic, not a clash-energy calculation or proof of favorable interactions.'),
 p('All 18 evaluated backbone omega angles were trans in the reference and each positive prediction. Mean circular absolute deviations were 3.43, 4.04 and 3.68 degrees for revision 1 and 9.42, 9.06 and 7.70 degrees for revision 2. Trans means absolute omega at least 150 degrees; circular differences correctly wrap at +/-180 degrees.'),
 p('Source: results/pose-audit/pose-audit.csv and pose-audit.json. Peptide residues 1-19 only; caps and GDP excluded from these contact, clash and omega metrics. This custom residue-contact recovery is not a DockQ score and adds no new selection threshold.','Fine'),PageBreak(),
 title('Independent Protenix diagnostic'),
 p('A subsequent cross-model diagnostic stress-tested the same two controls with Protenix after the Boltz gates had failed. Protenix-v2 stopped before prediction when its official checkpoint returned HTTP 403. The reachable base model completed six predictions (two controls x three seeds): the positive control recovered 0/41 native contacts in each seed (17, 42 and 101), scramble contact recovery is NA, positive-control core RMSDs were 29.06, 30.93 and 30.58 angstrom, and the chemistry checks failed.'),
 table(protenix_rows(),[W*.22,W*.17,W*.31,W*.30]),
 *maybe_fig('protenix-base-diagnostic.png'),
 h('Interpretation boundary'),p('The Protenix diagnostic is a model-family comparison and reference-recovery check. It adds no new pass threshold, no binder-discrimination claim and no candidate advancement. Its completed base-model outputs are descriptive diagnostics alongside the Boltz failures; the separate v2 access failure is retained as an upstream model-access limitation.'),
 p('Source: PROTOCOL_PROTENIX_DIAGNOSTIC.md and results/study-package/protenix-diagnostic-summary.json. Training overlap with 5XCO remains possible because the reference predates the 2021-09-30 cutoff.','Fine'),PageBreak(),
 title('Experimentally characterized benchmark candidates'),
 p('Primary literature provides a more defensible starting point for future controls than assuming a scramble is inactive. The table below reproduces reported assay values for the MP-1687 series. This is a distinct D-Cys/thioacetal family, with noncanonical modifications and different termini. None of these entries has been run in this campaign. [2]'),
 table([['Compound','Reported modification','GDP KRAS G12D\nTR-FRET EC50 nM']]+[[r['source_compound_id'],r['source_modification'],('> ' if r['relation']=='>' else '')+f"{int(r['value_nM']):,}"] for r in controls],[W*.2,W*.42,W*.38]),
 Spacer(1,12),p('Values reported as greater than 48,080 nM are right-censored assay results, not exact affinities. They must not be treated as 48,080 nM point estimates or as proof of zero binding. The parent is a 60 nM TR-FRET EC50 reference under that assay; the number is not its SPR KD.'),
 p('Exact molecular graphs, stereochemistry and assay conditions require verification before input generation. The cis D-Cys5-Pro6 bond described for a modified MP peptide must not be assigned to the original KRpep-2d control. The direct KRpep-2d alanine study independently identifies Leu7, Ile9 and Asp12 as important, but its abstract alone does not supply a complete, quantitative benchmark. [2,3]'),PageBreak(),
 title('Limits and the next scientific decision'),
 p('Published peptide-docking benchmarks report high-confidence incorrect poses and dependence on training examples. A 21 August 2026 cyclic-peptide preprint likewise separates pose generation from confidence ranking. These findings motivate independent pose/contact diagnostics; they do not demonstrate the mechanism of our failure or validate a binder classifier for this project. [4,5]'),
 h('Conditions for any further inference'),p('A new benchmark must use source-verified molecules and comparable assay labels, separate method development from evaluation, preserve the old failures, and declare its endpoints before outputs. A single bounded batch could be considered only after chemistry/model readiness and compute-budget checks. Main candidate screening remains conditional on a defensible validation outcome.'),
 h('Reproduction and release'),p('The repository contains original control structures, exact mappings, per-seed confidence, geometry audits, source-backed summaries, scripts and the local dashboard. In the tested Python 3.12 environment, the isolated export reproduced all checked files with identical hashes. This reproduces saved-data analyses; it does not rerun neural inference or constitute an independent biological validation. See README.md and results/reproducibility-qc.json.'),
 h('References'),
 p('[1] Sogabe et al. Crystal Structure of a Human K-Ras G12D Mutant in Complex with GDP and the Cyclic Inhibitory Peptide KRpep-2d. ACS Med Chem Lett, 2017. <link href="https://doi.org/10.1021/acsmedchemlett.7b00128" color="#176b87">doi:10.1021/acsmedchemlett.7b00128</link>.','Fine'),
 p('[2] Lim et al. Discovery of cell active macrocyclic peptides with on-target inhibition of KRAS signaling. Chemical Science, 2021. Table 2. <link href="https://doi.org/10.1039/D1SC05187C" color="#176b87">doi:10.1039/D1SC05187C</link>.','Fine'),
 p('[3] Niida et al. Investigation of the structural requirements of K-Ras(G12D) selective inhibitory peptide KRpep-2d using alanine scans and cysteine bridging. Bioorg Med Chem Lett, 2017. <link href="https://doi.org/10.1016/j.bmcl.2017.04.063" color="#176b87">doi:10.1016/j.bmcl.2017.04.063</link>.','Fine'),
 p('[4] Guan and Keating. Training bias and sequence alignments shape protein-peptide docking by AlphaFold and related methods. Protein Science, 2025. <link href="https://doi.org/10.1002/pro.70331" color="#176b87">doi:10.1002/pro.70331</link>.','Fine'),
 p('[5] Li et al. Benchmarking confidence estimation and rescoring for cyclic peptide-protein complex predictions. bioRxiv, 21 August 2026. <b>Preprint, not peer reviewed.</b> <link href="https://doi.org/10.64898/2026.08.20.746104" color="#176b87">doi:10.64898/2026.08.20.746104</link>.','Fine')]
build('KRpep-Zero-report.pdf',story)
brief=[title('KRpep-Zero study brief'),p('A reproducible study of chemistry and control validation','Deck'),
 p('<b>Main finding.</b> Full-molecule encoding corrected the measured chemical-geometry failures in the capped KRpep controls. It did not yield sufficient confidence separation or reliable experimental-pose recovery to support selecting novel binders. The independent Protenix diagnostic positive control recovered 0/41 native contacts in each seed (17, 42 and 101); scramble contact recovery is NA, and chemistry checks failed.'),
 table([['Evidence','Observed outcome'],['Reference','GDP-bound KRAS4B G12D 1-169 and KRpep-2d, PDB 5XCO'],['Actual model work','ESMC profiles; 2 rejected generator pilot structures; 18 control predictions total (12 Boltz + 6 Protenix)'],['Control identities','KRpep-2d positive and proposed scramble; runs are model samples, not biological replicates'],['Revision 2 chemistry','6/6 outputs: all 183 bonds in bounds and all 20 stereocenters correct'],['Revision 2 selection','Gap +0.0332 versus required +0.150; gate failed'],['Protenix base diagnostic','6/6 outputs; positive 0/41 each seed (17, 42, 101); scramble NA; RMSD 29.06 / 30.93 / 30.58 A; chemistry checks failed'],['Independent experiments','None performed in this campaign']],[W*.32,W*.68]),
 Spacer(1,12),h('Available analyses'),p('Use the all-18 table\'s View pose for one selected row. In the viewer set Model / representation to reference, v1, v2 or protenix, then choose Control and Seed; the UI shows one selected prediction plus the reference at a time. Use Reference peptide, Predicted target, Target surface and Prediction focus, then change Seed to compare runs. Inspect contact recovery and RMSD alongside the selected pose. The package contains source data, exact atom mappings, scripts, declared protocols and an offline reproduction receipt. The 18 predictions represent two control identities across model runs, not 18 independent peptides or biological replicates.'),
 h('What remains unresolved'),p('The scramble is not a demonstrated nonbinder. Published weak-binding analogs offer a better-supported future benchmark, but their modified chemistry must be verified first. No novel peptide, mutant selectivity, developability or therapeutic activity is established.'),
 p('Discussion focus: whether the proposed benchmark and pose metrics are sufficient for a subsequent candidate-selection study. The full report includes methods, all-seed figures, experimental control candidates and references.','Fine')]
build('KRpep-Zero-brief.pdf',brief)
print('Created research report and one-page study brief.')
