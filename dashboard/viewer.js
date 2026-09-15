/* Recorded coordinates only. Target-aligned assets are generated and checked in Python. */
(async function () {
  'use strict';
  const byId = id => document.getElementById(id);
  const select = {protocol: byId('protocol-select'), control: byId('control-select'), seed: byId('seed-select')};
  const response = await fetch('data/predictions.json');
  if (!response.ok) throw new Error('Prediction manifest unavailable');
  const manifest = await response.json();
  if (manifest.entries.length !== 18) throw new Error('Expected 18 recorded control predictions');
  const cache = new Map();
  const viewer = $3Dmol.createViewer('molecule', {backgroundColor:'#101f2c', antialias:true});
  window.moleculeViewer = viewer;
  const initialView = viewer.getView();
  let reference, predictedTarget, predictedPeptide, surface, selected = null;
  let showSurface = true, showReference = true, showTarget = false, spinning = false, busy = false;

  function setStatus(message) { byId('load-status').textContent = message; }
  function pressed(id, state) { byId(id).setAttribute('aria-pressed', String(state)); }
  function updateDisabled() {
    const isReference = select.protocol.value === 'reference';
    select.protocol.disabled = busy;
    select.control.disabled = busy || isReference;
    select.seed.disabled = busy || isReference;
    for (const id of ['whole','pocket','surface','reference-toggle','spin']) byId(id).disabled = busy;
    for (const id of ['prediction-focus','target-toggle']) byId(id).disabled = busy || isReference;
    document.querySelectorAll('.run-button').forEach(b => { b.disabled = busy; });
  }
  function styleModels() {
    reference.setStyle({}, {});
    reference.setStyle({chain:'A',hetflag:false}, {cartoon:{color:'#a0acb8'}});
    if (showReference) reference.setStyle({chain:'B'}, {stick:{color:'#ed5aa9',radius:0.20}});
    reference.setStyle({resn:'GDP'}, {stick:{color:'#f0c86a',radius:0.16}});
    reference.setStyle({chain:'A',resi:12}, {stick:{color:'#ff665e',radius:0.23},cartoon:{color:'#ff665e'}});
    if (predictedTarget) {
      predictedTarget.setStyle({}, {});
      if (showTarget) {
        predictedTarget.setStyle({chain:'A',hetflag:false}, {cartoon:{color:'#729bdf',opacity:0.65}});
        predictedTarget.setStyle({resn:'GDP'}, {stick:{color:'#f0c86a',radius:0.12}});
      }
    }
    if (predictedPeptide) predictedPeptide.setStyle({}, {stick:{color:'#65e5c3',radius:0.22}});
    viewer.render();
  }
  function fitAll() {
    viewer.setView(initialView);
    viewer.zoomTo();
    viewer.rotate(75,'y'); viewer.rotate(-25,'x'); viewer.render();
  }
  function showMetadata(entry) {
    byId('view-kicker').textContent = entry ? 'TARGET-ALIGNED PREDICTION + 5XCO' : 'EXPERIMENTAL REFERENCE';
    byId('view-title').textContent = entry ? `${entry.protocol_label} · ${entry.control_label} · seed ${entry.seed}` : '5XCO · KRAS G12D + KRpep-2d';
    byId('selected-name').textContent = entry ? `${entry.control_label} · seed ${entry.seed}` : 'Experimental KRpep-2d';
    byId('pose-value').textContent = entry?.core_rmsd_A == null ? '—' : entry.core_rmsd_A.toFixed(2);
    byId('contacts-value').textContent = !entry ? '41' : entry.native_contacts_recovered == null ? '—' : `${entry.native_contacts_recovered}/41`;
    byId('confidence-value').textContent = entry?.pair_iptm == null ? '—' : entry.pair_iptm.toFixed(4);
    byId('chemistry-status').textContent = entry ? entry.chemistry : '19 residues · Cys5–Cys15 disulfide · capped termini.';
    byId('selected-sequence').textContent = entry ? `Ac-${entry.sequence}-NH₂` : 'Ac-RRRR-CPLYISYDPVC-RRRR-NH₂';
    byId('viewer-note').textContent = entry ? 'Magenta: crystal peptide · Teal: prediction\nTarget-only alignment · no peptide refit' : 'Drag to rotate · scroll to zoom\nExperimental reference · no new design';
    byId('viewer-note').style.whiteSpace = 'pre-line';
    let note = 'Choose a model to compare a saved prediction with 5XCO. Seeds are listed in fixed numeric order, without confidence ranking.';
    if (entry?.control_id === 'SCRAMBLE-20260914') note = 'Proposed negative control; inactivity is unvalidated. Peptide RMSD and native-contact recovery are not assigned because its residue order differs from KRpep-2d.';
    else if (entry?.protocol === 'protenix') note = 'Independent diagnostic: all three positive seeds recover 0/41 native contacts. These results do not rescue either failed Boltz gate.';
    else if (entry) note = 'One of three retained seeds. A similar pose in one seed does not clear the control-selection gate. Compare confidence only within this Boltz revision.';
    byId('selection-note').textContent = note;
    byId('alignment-note').textContent = entry ? `Target-only fit: 169 matched Cα atoms · target RMSD ${entry.target_fit_rmsd_A.toFixed(3)} Å. Peptide connectivity follows the declared input graph; displayed coordinates were not relaxed or repaired.` : 'KRAS4B G12D residues 1–169, GDP state. Experimental structure at 1.25 Å resolution.';
    byId('download-cif').href = entry ? entry.raw_cif : 'data/structures/reference.cif';
    byId('download-cif').textContent = entry ? 'Download original prediction CIF ↗' : 'Download original reference CIF ↗';
    byId('provenance-text').textContent = entry ? `${manifest.alignment} Downloaded CIFs retain their original, unaligned coordinates. Source: ${entry.source_cif}` : 'Deposited experimental reference; no model inference.';
    byId('source-hash').textContent = `Source SHA-256: ${entry ? entry.source_sha256 : manifest.reference_sha256}`;
    document.querySelectorAll('[data-run]').forEach(row => row.setAttribute('data-selected', String(row.dataset.run === entry?.id)));
  }
  async function renderSelection() {
    if (busy) return;
    busy = true; updateDisabled();
    byId('molecule').setAttribute('aria-busy','true');
    setStatus('Loading recorded structure…');
    try {
      const isReference = select.protocol.value === 'reference';
      const entry = isReference ? null : manifest.entries.find(e => e.protocol === select.protocol.value && e.control_id === select.control.value && e.seed === Number(select.seed.value));
      if (!isReference && !entry) throw new Error('This recorded combination is unavailable');
      let payload;
      if (entry) {
        if (!cache.has(entry.id)) {
          const r = await fetch(entry.payload);
          if (!r.ok) throw new Error('Saved prediction could not be loaded');
          const data = await r.json();
          if (data.peptide_atoms.length !== 179) throw new Error('Peptide atom count mismatch');
          cache.set(entry.id, data);
        }
        payload = cache.get(entry.id);
      }
      viewer.spin(false); viewer.removeAllSurfaces(); viewer.removeAllModels(); viewer.removeAllLabels();
      reference = viewer.addModel(window.CAMPAIGN.pdb,'pdb');
      predictedTarget = null; predictedPeptide = null;
      if (payload) {
        predictedTarget = viewer.addModel(payload.target_pdb,'pdb');
        predictedPeptide = viewer.addModel();
        // 3Dmol may annotate input objects; preserve the immutable cached payload.
        predictedPeptide.addAtoms(JSON.parse(JSON.stringify(payload.peptide_atoms)));
      }
      selected = entry;
      styleModels();
      const created = await viewer.addSurface($3Dmol.SurfaceType.MS, {opacity:showSurface?0.55:0,color:'#879aa9'}, {model:reference,chain:'A',hetflag:false});
      surface = created.surfid;
      fitAll(); showMetadata(entry);
      if (spinning) viewer.spin('y',0.5);
      setStatus(entry ? 'Recorded coordinates loaded · no new inference' : 'Experimental reference loaded');
      window.STRUCTURE_READY = true;
      window.STRUCTURE_ERROR = null;
      byId('molecule').dataset.loadedRun = entry?.id || 'reference';
    } catch(error) {
      setStatus('Unable to load this view: ' + error.message);
      window.STRUCTURE_ERROR = error.message;
      window.STRUCTURE_READY = false;
    } finally {
      busy = false; updateDisabled();
      byId('molecule').setAttribute('aria-busy','false');
    }
  }
  Object.values(select).forEach(el => el.addEventListener('change', renderSelection));
  byId('whole').onclick = fitAll;
  byId('pocket').onclick = () => {viewer.zoomTo({model:reference,chain:'B'});viewer.zoom(0.75);viewer.render();};
  byId('prediction-focus').onclick = () => {if(predictedPeptide){viewer.zoomTo({model:predictedPeptide});viewer.zoom(0.70);viewer.render();}};
  byId('surface').onclick = () => {showSurface=!showSurface;viewer.setSurfaceMaterialStyle(surface,{opacity:showSurface?0.55:0,color:'#879aa9'});pressed('surface',showSurface);viewer.render();};
  byId('reference-toggle').onclick = () => {showReference=!showReference;pressed('reference-toggle',showReference);styleModels();};
  byId('target-toggle').onclick = () => {showTarget=!showTarget;pressed('target-toggle',showTarget);styleModels();};
  byId('spin').onclick = () => {spinning=!spinning;pressed('spin',spinning);viewer.spin(spinning?'y':false,0.5);};
  document.querySelectorAll('.run-button').forEach(button => button.addEventListener('click',async()=>{
    const entry=manifest.entries.find(e=>e.id===button.dataset.runId);
    if (!entry || busy) return;
    select.protocol.value=entry.protocol;select.control.value=entry.control_id;select.seed.value=String(entry.seed);
    document.getElementById('structure').scrollIntoView({behavior:'instant',block:'start'});
    await renderSelection();
  }));
  // Figures expand without changing any measured value or loading external assets.
  const dialog=document.createElement('dialog');dialog.className='image-dialog';
  dialog.innerHTML='<button type="button" aria-label="Close enlarged figure">Close ✕</button><p id="figure-caption"></p><div class="image-scroll"><img alt=""></div>';
  dialog.setAttribute('aria-labelledby','figure-caption');document.body.append(dialog);
  dialog.querySelector('button').onclick=()=>dialog.close();
  document.querySelectorAll('img.figure').forEach(img=>{
    img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label','Enlarge figure: '+img.alt);
    const open=()=>{dialog.querySelector('img').src=img.src;dialog.querySelector('img').alt=img.alt;byId('figure-caption').textContent=img.alt;dialog.showModal();};
    img.addEventListener('click',open);img.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});
  });
  await renderSelection();
})().catch(error=>{
  const status=document.getElementById('load-status');
  if(status)status.textContent='Viewer unavailable: '+error.message;
  window.STRUCTURE_ERROR=error.message;
  window.STRUCTURE_READY=false;
});
