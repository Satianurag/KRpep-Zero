"""Rebuild recorded-data figures/dashboard locally. No inference or API keys."""
from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[1]
if (root/'release-manifest.json').exists():
    from export_public import verify_existing
    verify_existing(root)
scripts=['define_target.py','align_ras.py','plot_campaign.py','plot_esm.py','analyze_controls.py','plot_controls.py','report_controls.py']
if (root/'results/control-remediation-v2-002/extracted/metadata.json').exists():
    scripts += ['check_reference_graph.py','analyze_controls_v2.py','report_controls_v2.py']
scripts += ['audit_saved_poses.py','plot_pose_audit.py','curate_study_evidence.py']
protenix_meta=root/'results/protenix-base-default-diagnostic-001/extracted/metadata.json'
if protenix_meta.exists() and not json.loads(protenix_meta.read_text()).get('error'):
    scripts += ['analyze_protenix_controls.py','plot_protenix_diagnostic.py']
scripts += ['summarize_protenix.py','build_dashboard.py']
for script in scripts:
    print('Reproducing',script,flush=True)
    subprocess.run([sys.executable,str(root/'analysis'/script)],cwd=root,check=True)
print('Rebuilt recorded-data figures and dashboard. Model inference was not rerun.')
