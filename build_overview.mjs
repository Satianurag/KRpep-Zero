import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const { Presentation, PresentationFile } = await import('/Users/Apple/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs');

const root = path.dirname(fileURLToPath(import.meta.url));
const skillDir = '/Users/Apple/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations';
const buildDir = path.join(root, '.deck-build');
const outDir = path.join(root, 'output/presentation');
await fs.mkdir(buildDir, {recursive:true});
await fs.mkdir(outDir, {recursive:true});
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(pathToFileURL(path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
const font = resolvePresentationFont({sourceFont:'Aptos'});
const C = { navy:'#0B1F33', ink:'#162B3D', teal:'#16B8A6', cyan:'#6ED6D0', magenta:'#E75288', gold:'#E7B75C', bg:'#F5F8FA', slate:'#5A7184', line:'#D5E0E7', white:'#FFFFFF', red:'#D9545D' };
const W=1280,H=720;
const pres = Presentation.create({slideSize:{width:W,height:H}});
async function readJson(rel,fallback){
  try{return JSON.parse(await fs.readFile(path.join(root,rel),'utf8'));}
  catch{return fallback;}
}
const protenixSummary=await readJson('results/study-package/protenix-diagnostic-summary.json',{attempts:[]});

function rect(slide,x,y,w,h,fill,line='none',radius=0){
  return slide.shapes.add({geometry: radius? 'roundRect':'rect', position:{left:x,top:y,width:w,height:h}, fill, line:{fill:line,width:line==='none'?0:1}, ...(radius?{borderRadius:radius}: {})});
}
function text(slide,txt,x,y,w,h,size=20,color=C.ink,bold=false,opts={}){
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=txt; s.text.style={typeface:font,fontSize:size,color,bold,autoFit:'shrink',...(opts.italic?{italic:true}:{}),...(opts.align?{align:opts.align}:{})};
  return s;
}
function base(title, kicker){
  const s=pres.slides.add(); s.background.fill=C.bg; rect(s,0,0,W,12,C.teal); text(s,kicker||'KRpep-Zero  /  research validation',60,28,900,24,15,C.teal,true); text(s,title,60,56,1120,56,34,C.navy,true); text(s,'15 September 2026',1020,30,200,20,14,C.slate,false,{align:'right'}); return s;
}
function notes(slide,body){slide.speakerNotes.textFrame.setText(body);}
function fmt(v,n=3){return Number(v).toFixed(n)}
function friendlyStatus(status){
  return ({
    failed_before_prediction:'failed before prediction',
    failed_with_partial_outputs:'failed with partial outputs',
    returned_without_expected_outputs:'returned without expected outputs',
    pending_or_unreturned:'not returned',
    completed:'completed',
    missing:'not returned',
  })[status] || status || 'not returned';
}

// 1 Cover
{ const s=pres.slides.add(); s.background.fill=C.navy; rect(s,0,0,W,16,C.teal); rect(s,820,0,460,H,'#102B43');
  text(s,'KRpep-Zero',72,118,700,76,52,C.white,true); text(s,'Chemistry and control validation for KRAS peptide modeling',76,208,690,80,28,C.cyan,false); text(s,'Study overview  |  15 September 2026',78,330,560,28,19,C.white,false); text(s,'Decision-ready evidence from 18 retained control predictions',78,446,720,30,20,'#D8E8EE',false); text(s,'12 Boltz + 6 Protenix  |  2 control identities',78,482,720,26,17,'#D8E8EE',false);
  rect(s,870,150,250,250,'none',C.teal,125); rect(s,920,200,150,150,'none',C.magenta,75); text(s,'STOP',920,256,150,36,30,C.white,true,{align:'center'}); text(s,'separation gate failed',852,430,290,28,17,C.white,false,{align:'center'}); notes(s,'Scope: computational validation study around a GDP-state KRAS G12D reference. This deck reports recorded outcomes and limits; it does not claim a binder or therapeutic result.'); }

// 2 reference
{ const s=base('Target reference and positive control','01  /  reference identity');
  text(s,'The benchmark molecule is KRpep-2d bound to GDP-state KRAS G12D in 5XCO.',60,126,1080,30,20,C.ink,false);
  const img=await fs.readFile(path.join(root,'dashboard/assets/5xco-reference.png')); s.images.add({blob:img,contentType:'image/png',alt:'5XCO KRpep-2d reference',fit:'contain',position:{left:60,top:188,width:470,height:320}});
  text(s,'KRpep-2d',580,192,260,32,25,C.navy,true); text(s,'Ac-RRRRCPLYISYDPVCRRRR-NH2',580,232,530,28,19,C.magenta,true); text(s,'19 residues  |  Cys5–Cys15 disulfide  |  N-acetyl  |  C-terminal amide',580,270,580,28,17,C.slate,false);
  const t=s.tables.add({rows:4,columns:4,left:580,top:332,width:600,height:150,values:[['Assay','KRAS G12D','KRAS WT','WT / G12D'],['SPR KD, GDP','8.9 nM','58 nM','6.52×'],['SPR KD, GTP','11 nM','200 nM','18.18×'],['Meaning','affinity','affinity','arithmetic ratio']]});
  t.style='Table Grid'; t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.navy,textStyle:{color:C.white,bold:true,fontSize:15}}); t.cells.block({row:1,column:0,rowCount:3,columnCount:4}).assign({textStyle:{fontSize:15,color:C.ink}});
  text(s,'Source: Sogabe et al. 2017, 5XCO / crystal paper. Ratios are arithmetic from Table 1.',580,512,600,24,13,C.slate,false);
  notes(s,'Primary source: Sogabe et al., 2017, PMID 28740607, DOI 10.1021/acsmedchemlett.7b00128; RCSB 5XCO. The displayed assay ratios are arithmetic from the published SPR KD values.'); }

// 3 workflow
{ const s=base('Validation workflow and ESMC context','02  /  method boundary');
  text(s,'The campaign moved from sequence diagnostics to two control revisions, then stopped at the declared gate.',60,124,1120,30,20,C.ink,false);
  const steps=[['01','Reference','5XCO + GDP-state KRAS4B 1–169'],['02','Sequence','ESMC300M profile, seed 17'],['03','Boltz controls','12 runs: 2 identities x 3 seeds x 2 representations'],['04','Protenix check','6 runs: 2 identities x 3 seeds; chemistry failed'],['05','Decision','No candidate generation after failed separation']];
  let y=194; for(const [n,h,b] of steps){rect(s,70,y,92,62,C.navy,'none',16); text(s,n,70,y+14,92,24,18,C.cyan,true,{align:'center'}); text(s,h,190,y+2,220,28,21,C.navy,true); text(s,b,190,y+32,760,24,17,C.slate,false); if(y<530) rect(s,115,y+64,3,30,C.teal); y+=88;}
  rect(s,930,190,250,340,'#E9F7F5','none',20); text(s,'What ESMC can support',960,220,190,26,19,C.teal,true); text(s,'Sequence-model diagnostics\n\nMasked-logit profile\n\nNo pocket affinity\n\nNo binding classifier',960,270,180,180,18,C.ink,false);
  notes(s,'ESMC300M is a sequence-model diagnostic. It does not measure pocket affinity. Method context from PROVENANCE.md and the retained ESMC metadata.'); }

// 4 v1
{ const s=base('Revision 1: confidence did not separate the controls','03  /  v1 gate');
  text(s,'The positive and proposed scramble scored almost identically across all three seeds.',60,124,1100,30,20,C.ink,false);
  const chart=s.charts.add('bar',{position:{left:70,top:190,width:680,height:360},categories:['Seed 17','Seed 42','Seed 101'],series:[{name:'KRpep-2d',values:[0.909436,0.946232,0.899421],fill:C.teal},{name:'SCRAMBLE',values:[0.906377,0.939061,0.921256],fill:C.magenta}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,dataLabels:{showValue:true,position:'outEnd'}}); applyPresentationChartFont(chart,{fontFamily:font});
  rect(s,800,190,380,130,C.navy,'none',18); text(s,'Mean gap',828,216,140,22,17,C.cyan,true); text(s,'−0.003868',828,248,300,44,36,C.white,true); text(s,'required  ≥  +0.15',828,292,250,22,17,C.white,false);
  text(s,'Outcome',800,370,140,24,17,C.magenta,true); text(s,'Positive exceeded scramble in 2/3 seeds, but the mean-gap criterion failed. No seeds were dropped or repeated.',800,404,350,92,20,C.ink,false);
  text(s,'Confidence is not affinity. The scramble was a proposed negative control, not an experimentally established nonbinder.',800,530,350,68,16,C.slate,false);
  notes(s,'Source: results/CALIBRATION_REPORT.md and dashboard/data/per-seed.csv. Pair ipTM is the arithmetic mean of parsed directional fields after chain mapping checks.'); }

// 5 v2 chemistry
{ const s=base('Revision 2: chemistry repair passed the declared checks','04  /  v2 representation');
  text(s,'Full molecular graphs preserved the intended control identities across every saved prediction.',60,124,1110,30,20,C.ink,false);
  const t=s.tables.add({rows:5,columns:5,left:60,top:192,width:760,height:240,values:[['Control','Seeds','Bonds in bounds','Stereocenters','Critical links'],['KRpep-2d','17 · 42 · 101','183 / 183','20 / 20','PASS'],['SCRAMBLE-20260914','17 · 42 · 101','183 / 183','20 / 20','PASS'],['Gate','all six','100%','100%','PASS'],['Meaning','','geometry only','','not biological activity']]});
  t.style='Table Grid'; t.cells.block({row:0,column:0,rowCount:1,columnCount:5}).assign({fill:C.navy,textStyle:{color:C.white,bold:true,fontSize:15}}); t.cells.block({row:1,column:0,rowCount:4,columnCount:5}).assign({textStyle:{fontSize:15,color:C.ink}});
  rect(s,880,192,300,315,'#E9F7F5','none',18); text(s,'What changed',910,220,220,24,19,C.teal,true); text(s,'Complete SMILES / graph input',910,265,230,30,17,C.ink,false); text(s,'183 molecular bonds checked',910,335,230,30,17,C.ink,false); text(s,'20 mapped stereocenters',910,405,230,30,17,C.ink,false); text(s,'All six outputs retained',910,475,230,30,17,C.ink,false);
  text(s,'Chemistry pass supports representation integrity under these checks. It does not validate molecular energy or biological activity.',60,565,1050,32,18,C.slate,false);
  notes(s,'Source: results/REMEDIATION_V2_REPORT.md; results/control-remediation-v2-002/; PROTOCOL_REMEDIATION_V2.md. Chemistry pass means all 183 bonds and 20 stereocenters passed in every seed.'); }

// 6 v2 gate
{ const s=base('Revision 2: chemistry passed, separation still failed','05  /  v2 gate');
  text(s,'The within-revision mean confidence gap remained below the preregistered threshold.',60,124,1140,30,20,C.ink,false);
  const chart=s.charts.add('bar',{position:{left:70,top:190,width:650,height:340},categories:['Seed 17','Seed 42','Seed 101'],series:[{name:'Positive core Cα RMSD (Å)',values:[21.3955,12.2365,11.0290],fill:C.teal}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,dataLabels:{showValue:true,position:'outEnd'}}); applyPresentationChartFont(chart,{fontFamily:font});
  rect(s,780,192,400,132,C.navy,'none',18); text(s,'Observed gap',810,216,180,20,17,C.cyan,true); text(s,'+0.033214',810,246,300,42,36,C.white,true); text(s,'required  ≥  +0.150',810,288,240,20,17,C.white,false);
  const t=s.tables.add({rows:4,columns:4,left:780,top:362,width:400,height:150,values:[['Seed','Positive','Scramble','Δ'],['17','0.5640','0.6509','−0.0870'],['42','0.6490','0.4855','+0.1636'],['101','0.6569','0.6338','+0.0230']]}); t.style='Table Grid'; t.cells.block({row:0,column:0,rowCount:1,columnCount:4}).assign({fill:C.navy,textStyle:{color:C.white,bold:true,fontSize:14}}); t.cells.block({row:1,column:0,rowCount:3,columnCount:4}).assign({textStyle:{fontSize:14,color:C.ink}});
  text(s,'Positive wins 2/3 paired seeds. The mean-gap criterion fails.',780,542,390,30,18,C.magenta,true);
  notes(s,'Source: results/REMEDIATION_V2_REPORT.md and dashboard/data/v2-gate-summary.json. Positive core RMSDs after fitting target Cα1–169: 21.3955, 12.2365, 11.0290 Å for seeds 17, 42, 101.'); }

// 7 literature and limits
{ const s=base('Next benchmark: verified controls before any new inference','06  /  literature and limits');
  text(s,'The evidence supports a bounded benchmark plan, not a claim of generalization.',60,124,1100,30,20,C.ink,false);
  text(s,'Literature anchors',70,188,300,26,21,C.teal,true); text(s,'Lim et al. (2021)\nDisulfide / thioacetal chemistry changes the molecule and assay context.\n\nGuan & Keating (2025)\nHigh-confidence incorrect peptide poses show confidence can mislead.\n\nLi et al. (2026, preprint)\nPose confidence and ranking are separate questions in cyclic-peptide benchmarks.',70,228,510,300,18,C.ink,false);
  rect(s,650,182,530,350,'#EAF0F5','none',18); text(s,'Boundaries for the next benchmark',685,212,440,26,21,C.navy,true); text(s,'• Verify exact chemistry and assay meaning for every control\n• Keep pose metrics separate from confidence and binding\n• Treat 18 runs as model runs of 2 identities, not biological replicates\n• Use declared criteria before any new outputs\n• Stop after the bounded batch if the gate remains inconclusive',685,260,440,210,18,C.ink,false);
  text(s,'Discussion focus: are the verified controls and pose metrics sufficient for a later candidate-selection study?',70,570,1120,28,17,C.magenta,true);
  notes(s,'Primary literature: Lim et al., PMC8672774; Guan/Keating, PMC12518507, DOI 10.1002/pro.70331; Li et al., 2026, unreviewed preprint, DOI 10.64898/2026.08.20.746104.'); }

// 8 conclusion
{ const s=base('Conclusion and reproducible decision','07  /  handoff');
  text(s,'Chemistry repair improved input integrity. Control separation remains insufficient for candidate selection.',60,126,1130,42,24,C.navy,true);
  rect(s,70,220,330,170,C.navy,'none',18); text(s,'DECISION',100,248,180,22,17,C.cyan,true); text(s,'STOP',100,282,250,48,40,C.white,true); text(s,'No candidate-generation claim',100,340,240,22,17,C.white,false);
  text(s,'Repro package',480,220,250,26,21,C.teal,true); text(s,'18 retained control predictions\n12 Boltz + 6 Protenix\nPer-seed CSVs and gate summaries\nSaved structures and hashes\nOffline reproduction checks',480,264,320,180,19,C.ink,false);
  text(s,'Dashboard guide',870,220,260,26,21,C.teal,true); text(s,"Use the all-18 table's View pose for one selected row. Set Model / representation to reference, v1, v2 or protenix, then choose Control and Seed. The UI shows one selected prediction plus the reference at a time. Use Reference peptide, Predicted target, Target surface and Prediction focus; change Seed to compare runs.",870,264,300,210,16,C.ink,false);
  text(s,'Discussion framing: chemistry integrity improved, but confidence separation and reference-pose recovery remain inadequate for candidate selection.',70,510,1080,40,18,C.magenta,true);
  notes(s,'Conclusion from PROVENANCE.md and v2 report. This is a reproducible validation study; successful binder discovery is not established.'); }

// 9 Protenix diagnostic addendum
{ const s=base('Protenix diagnostic addendum','08  /  independent model check');
  text(s,'A separate Protenix diagnostic completed six runs after the Boltz gates had already failed. It adds evidence, not candidate selection.',60,124,1120,38,20,C.ink,false);
  const attempts=protenixSummary.attempts || [];
  const first=attempts[0] || {};
  const second=attempts[1] || {};
  rect(s,70,194,520,168,C.navy,'none',18);
  text(s,'Protenix-v2',104,222,260,26,22,C.cyan,true);
  text(s,friendlyStatus(first.status || 'not returned'),104,260,320,32,25,C.white,true);
  text(s,`Output: ${first.prediction_cif_count ?? 0} CIFs`,104,306,210,24,18,C.white,false);
  text(s,first.label === 'Protenix-v2' ? 'Checkpoint HTTP 403 before prediction' : (first.error || 'No error receipt yet'),324,306,220,42,15,'#D8E8EE',false);
  rect(s,690,194,520,168,'#EAF7F4','none',18);
  text(s,'Full base fallback',724,222,260,26,22,C.teal,true);
  text(s,friendlyStatus(second.status || 'completed'),724,260,320,32,25,C.navy,true);
  text(s,`Model: ${second.model || 'protenix_base_default_v1.0.0'}`,724,306,380,24,17,C.ink,false);
  text(s,`Output: ${second.prediction_cif_count ?? 0} CIFs`,724,334,220,24,17,C.ink,false);
  const rmsd=second.positive_core_rmsd_A ? second.positive_core_rmsd_A.map(v=>Number(v).toFixed(2)).join(' / ') : '29.06 / 30.93 / 30.58';
  const t=s.tables.add({rows:4,columns:3,left:80,top:405,width:1120,height:135,values:[['Question','Current evidence','Boundary'],['Why not v2?','Official checkpoint returned HTTP 403 before model load','No v2 predictions were produced'],['Base result',`6 CIFs; positive 0/41 each seed (17, 42, 101); scramble NA; RMSD ${rmsd}`,'Chemistry checks failed'],['Research use','One selected prediction + reference; change Seed to compare runs','Descriptive only; no new gate']]});
  t.style='Table Grid';
  t.cells.block({row:0,column:0,rowCount:1,columnCount:3}).assign({fill:C.navy,textStyle:{color:C.white,bold:true,fontSize:14}});
  t.cells.block({row:1,column:0,rowCount:3,columnCount:3}).assign({textStyle:{fontSize:12.5,color:C.ink}});
  text(s,'Protenix base positive control recovered 0/41 native contacts in each seed; scramble is NA. Chemistry checks failed and the Boltz stop decision remains unchanged.',80,616,1080,28,18,C.magenta,true);
  notes(s,'Source: PROTOCOL_PROTENIX_DIAGNOSTIC.md and results/study-package/protenix-diagnostic-summary.json. Protenix-v2 failed at upstream checkpoint download with HTTP 403 before scientific outputs. The completed base diagnostic produced six CIFs, 0/41 native contacts in seeds 17, 42 and 101, positive-control core RMSDs 29.06 / 30.93 / 30.58 Å, and failed chemistry checks.'); }

const candidate=path.join(buildDir,'candidate-overview.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidate);
const finalPath=path.join(outDir,'KRpep-Zero-overview.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,pythonExecutable:'/Users/Apple/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','2','--require-native-table-slide','5','--require-native-table-slide','6'],requiredNativeTableOwnerSlides:[2,5,6],requiredNativeChartOwnerSlides:[4,6],materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,receiptPath:path.join(buildDir,'validation-v6-final.json'),explicitTotalSlideCount:9});
console.log(JSON.stringify({finalPath,result},null,2));
