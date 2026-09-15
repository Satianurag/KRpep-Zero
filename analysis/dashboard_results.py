"""Render the recorded calibration outcome into the static evidence dashboard."""
import csv,json,shutil

def add_remediation(html,root,dashboard):
    source=root/'results/remediation/status.json'
    if not source.exists():return html
    status=json.loads(source.read_text())
    shutil.copy2(source,dashboard/'data/remediation-status.json')
    shutil.copy2(root/'PROTOCOL_REMEDIATION_V2.md',dashboard/'reports/PROTOCOL_REMEDIATION_V2.md')
    card='''<section id="remediation"><div class="section-head"><h2>Testing a repair to the method</h2><span class="tag">REVISION 2 · RUNNING</span></div><div class="card card-pad" style="border-color:#397767"><div class="eyebrow">The original failure remains in the record</div><h2 style="margin-top:10px">Keep the peptide as one complete chemical graph.</h2><p>The first representation left gaps in bond-geometry guidance. The documented full-molecule route now carries both distance bounds for the cap links and disulfide. Both controls passed input checks for all 183 peptide bonds and 20 stereocenters.</p><div class="grid2" style="margin:18px 0"><div><h3>What is running</h3><p class="small">The same positive and proposed scramble, each with seeds 17, 42 and 101. One GPU worker; pinned model; no affinity inference.</p></div><div><h3>What must pass</h3><p class="small">The unchanged +0.150 mean-confidence separation rule, plus retained stereochemistry and credible critical-link geometry in every output. Neural results are pending.</p></div></div><a href="reports/PROTOCOL_REMEDIATION_V2.md">Read the protocol declared before this batch ↗</a></div></section>'''
    if status['state']=='RUNNING':
        html=html.replace('<section id="campaign">',card+'<section id="campaign">',1)
        html=html.replace('CONTROL GATE FAILED','METHOD REPAIR IN PROGRESS')
        html=html.replace('A failed control gate. A clear next decision.','Testing the method before choosing a peptide.')
        html=html.replace('Six control predictions expose confidence overlap, pose variability and cap-geometry problems.','The first controls exposed a problem. A preregistered chemistry-representation repair is now under test.')
        html=html.replace('Control calibration: stop decision','Revision 1: the recorded stop decision')
    elif status['state'] in ('PASSED','FAILED'):
        result=root/'results/control-remediation-v2-002/analysis'
        gate=json.loads((result/'gate-summary.json').read_text())
        rows=list(csv.DictReader((result/'per-seed.csv').open()))
        assert (status['state']=='PASSED')==gate['passed']
        for name in ('gate-summary.json','per-seed.csv','structure-audit.json'):
            shutil.copy2(result/name,dashboard/'data'/('v2-'+name))
        shutil.copy2(root/'results/REMEDIATION_V2_REPORT.md',dashboard/'reports/REMEDIATION_V2_REPORT.md')
        title='Both gates pass. Candidate work can proceed.' if gate['passed'] else 'The repaired method still cannot support candidate selection.'
        decision='The preregistered controls permit main generation. No novel peptide activity is established.' if gate['passed'] else 'The second calibration failed. The candidate pipeline remains stopped under the declared protocol.'
        entries=''
        for r in rows:
            entries+=f"<tr><td>{'KRpep-2d' if r['control_id']=='KRpep-2d' else 'Proposed scramble'}</td><td>{r['seed']}</td><td>{float(r['pair_iptm_mean']):.4f}</td><td>{'PASS' if r['critical_links_passed']=='True' else 'FAIL'}</td><td>{'PASS' if r['stereochemistry_passed']=='True' else 'FAIL'}</td><td>{float(r['fraction_bonds_within_bounds']):.1%}</td></tr>"
        card=f'''<section id="remediation"><div class="section-head"><h2>Revision 2: the chemistry repair result</h2><span class="tag">6 / 6 RUNS COMPLETE</span></div><div class="card card-pad" style="border-color:#897448"><div class="eyebrow">The original failure remains in the record</div><h2 style="margin-top:10px">{title}</h2><p>{decision}</p><div class="result-metrics"><div><strong>{gate['positive_minus_scramble']:+.4f}</strong><span>Mean confidence gap · requires ≥ +0.150</span></div><div><strong>{'PASS' if gate['separation_passed'] else 'FAIL'}</strong><span>Control separation</span></div><div><strong>{'PASS' if gate['chemistry_passed'] else 'FAIL'}</strong><span>Critical links + all stereocenters</span></div></div><p class="small">The same controls were represented as complete molecular graphs. Compare seeds within this revision; absolute confidence cannot be compared with revision 1 because tokenization changed.</p><a href="reports/REMEDIATION_V2_REPORT.md">Read the result and limitations ↗</a> · <a href="reports/PROTOCOL_REMEDIATION_V2.md">Frozen revision-2 protocol ↗</a></div><div class="card" style="margin-top:18px"><img class="figure" src="assets/control-remediation-v2.png" alt="All six full-graph control predictions, unchanged confidence gate, bond and stereochemistry checks, and positive-control pose diagnostics"><div class="caption">These are computational diagnostics. The scramble remains an unvalidated negative proposal; no binding affinity or biological activity is inferred.</div></div><div class="card" style="margin-top:18px"><div class="card-top"><h3>Every revision-2 seed</h3><a class="small" href="data/v2-per-seed.csv" download>Download CSV ↗</a></div><div class="table-scroll"><table><thead><tr><th>Molecule</th><th>Seed</th><th>Pair ipTM</th><th>Critical links</th><th>All 20 centers</th><th>All bonds in bounds</th></tr></thead><tbody>{entries}</tbody></table></div><div class="caption">Bond coverage is reported across all 183 bonds. The declared chemistry gate requires all three critical links and all 20 stereocenters to pass in every output.</div></div></section>'''
        html=html.replace('<section id="campaign">',card+'<section id="campaign">',1)
        html=html.replace('CONTROL GATE FAILED','CONTROL REPAIR PASSED' if gate['passed'] else 'CONTROL REPAIR FAILED')
        html=html.replace('A failed control gate. A clear next decision.','The method has been tested. Every result is visible.')
        html=html.replace('Six control predictions expose confidence overlap, pose variability and cap-geometry problems.','Twelve control predictions, two declared protocols, and a documented decision before candidate selection.')
        html=html.replace('Control calibration: stop decision','Revision 1: the recorded stop decision')
    return html

def add_results(html, root, dashboard):
    gatefile=root/'results/controls/gate-summary.json'
    if not gatefile.exists():return html
    g=json.loads(gatefile.read_text())
    rows=list(csv.DictReader((root/'results/controls/per-seed.csv').open()))
    assert not g['passed'], 'Update outcome presentation explicitly if a new protocol is authorized.'
    for source in [root/'results/CALIBRATION_REPORT.md',root/'PROTOCOL.md',root/'PROVENANCE.md']:
        shutil.copy2(source,dashboard/'reports'/source.name)
    data=dashboard/'data'; data.mkdir(exist_ok=True)
    for filename in ('per-seed.csv','gate-summary.json','structure-audit.json'):
        shutil.copy2(root/'results/controls'/filename,data/filename)
    entries=''.join(f"<tr><td>{'KRpep-2d' if r['control_id']=='KRpep-2d' else 'Proposed scramble'}</td><td>{r['seed']}</td><td>{float(r['pair_iptm_mean']):.4f}</td><td>{float(r['interface_CA_plddt_0_to_100']):.2f}</td><td>{float(r['peptide19_C_NH2_N_A']):.3f}</td></tr>" for r in rows)
    panel=f'''<section id="campaign"><div class="section-head"><h2>Control calibration: stop decision</h2><span class="tag">6 / 6 RUNS COMPLETE</span></div>
    <div class="card card-pad" style="border-color:#895b48"><div class="eyebrow" style="color:var(--gold)">Predeclared QC gate failed</div><h2 style="margin-top:10px">The scramble scores as highly as the positive control.</h2>
    <p>Mean pair-ipTM gap <strong style="color:var(--gold)">{g['positive_minus_scramble']:+.4f}</strong>; required ≥ +0.150. Positive wins 2/3 paired seeds, but the mean-gap criterion fails. Further screening is stopped.</p>
    <div class="result-metrics"><div><strong>{g['positive_mean_pair_iptm']:.3f}</strong><span>KRpep-2d mean</span></div><div><strong>{g['scramble_mean_pair_iptm']:.3f}</strong><span>Proposed scramble mean</span></div><div><strong>0 / 2</strong><span>Generator calibration filter passes</span></div></div>
    <a href="reports/CALIBRATION_REPORT.md">Read the complete decision and limitations ↗</a></div>
    <div class="card" style="margin-top:18px"><img class="figure" src="assets/control-calibration.png" alt="Six-seed confidence comparison, failed predeclared gate, positive-control pose RMSD and terminal-cap geometry"><div class="caption">All seeds retained. Pair confidence, crystal-pose recovery and chemical geometry answer different questions. The proposed scramble is not an experimentally established nonbinder.</div></div>
    <div class="card" style="margin-top:18px"><div class="card-top"><h3>Every control seed</h3><a class="small" href="data/per-seed.csv" download>Download CSV ↗</a></div><div class="table-scroll"><table><thead><tr><th>Molecule</th><th>Seed</th><th>Pair ipTM</th><th>Interface pLDDT</th><th>Cap C–N (Å)</th></tr></thead><tbody>{entries}</tbody></table></div><div class="caption">pLDDT uses a 0–100 scale; pair ipTM is the mean of A→B and B→A. Cap geometry is a post-run diagnostic, not a revised gate.</div></div>
    <div class="grid2" style="margin-top:18px"><div class="card card-pad"><div class="eyebrow">Generation calibration</div><h3 style="margin-top:10px">Two structures, zero accepted designs</h3><p class="small">15- and 13-residue backbone cycles retained GDP and closed geometrically. Both failed the built-in glycine-content and RMSD filters. The primary 60-design batch was not launched.</p><div class="sequence">MITEDGGLTSGIVGG<br>PGGTAPGLPLAGP</div><p class="small">Rejected calibration outputs; no top design selected.</p></div>
    <div class="card card-pad"><div class="eyebrow">Downstream status</div><h3 style="margin-top:10px">Selectivity and developability remain untested</h3><p class="small">The control gate stopped candidate screening, WT comparisons, developability triage and assay drafting. No biological selectivity or novel binding activity is established.</p><div class="callout">A revised campaign requires a newly declared protocol and independently justified controls. This failed calibration remains part of the record.</div></div></div>
    <div class="stages" style="margin-top:18px"><div class="stage complete"><strong>01</strong><b>Evidence</b><small>Sources verified</small></div><div class="stage complete"><strong>02</strong><b>Target</b><small>169 residues checked</small></div><div class="stage complete"><strong>03</strong><b>ESMC</b><small>Technical QC passed</small></div><div class="stage active"><strong>04</strong><b>Generation</b><small>2 calibration · 0 pass</small></div><div class="stage active"><strong>05</strong><b>Controls</b><small>6 runs · gate failed</small></div><div class="stage"><strong>06</strong><b>Developability</b><small>Stopped by gate</small></div><div class="stage"><strong>07</strong><b>Assay draft</b><small>Stopped by gate</small></div><div class="stage complete"><strong>08</strong><b>Report</b><small>Failure documented</small></div></div></section>'''
    start=html.index('<section id="campaign">'); end=html.index('<section><h2>Read the evidence',start)
    html=html[:start]+panel+'\n'+html[end:]
    html=html.replace('RESEARCH IN PROGRESS','CONTROL GATE FAILED')
    html=html.replace('The pocket, before the prediction.','A failed control gate. A clear next decision.')
    html=html.replace('Experimental reference and computational checks for a reproducible design campaign.','Six control predictions expose confidence overlap, pose variability and cap-geometry problems.')
    html=html.replace('Crystal coordinates · no designed peptide yet','Experimental reference · not a new design')
    html=html.replace('The computational experiment remains in progress.','This campaign stopped at its predeclared control gate.')
    html=html.replace('<div class="files">','<div class="files"><a href="reports/CALIBRATION_REPORT.md">Calibration report ↗</a><a href="reports/PROTOCOL.md">Frozen protocol ↗</a><a href="reports/PROVENANCE.md">Provenance ↗</a><a href="data/gate-summary.json">Gate data ↗</a><a href="data/artifact-manifest.json">Artifact hashes ↗</a>',1)
    html=html.replace('</style>','.result-metrics{display:flex;gap:45px;flex-wrap:wrap;margin:22px 0}.result-metrics strong{display:block;font:36px ui-monospace,monospace;color:var(--gold)}.result-metrics span{font-size:12px;color:var(--muted)}.table-scroll{overflow-x:auto}@media(max-width:600px){.section-head{align-items:start;gap:10px;flex-direction:column}.result-metrics{gap:20px}.result-metrics strong{font-size:29px}}\n</style>')
    return add_remediation(html,root,dashboard)
