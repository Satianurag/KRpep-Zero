"""Check positive-control atom identity and links against the deposited reference."""
from pathlib import Path
import hashlib,json
import gemmi

root=Path(__file__).resolve().parents[1]
reference=root/'results/target/5xco-reference.cif'
structure=gemmi.read_structure(str(reference))
graphs=json.loads((root/'results/remediation/full-molecule/graphs.json').read_text())
item=next(x for x in graphs['controls'] if x['id']=='KRpep-2d')
expected={(x['peptide_author_residue'],x['atom_name'],x['element']) for x in item['atom_map']}
actual={(r.seqid.num,a.name,a.element.name) for r in structure[0]['B'] for a in r
        if not a.element.is_hydrogen and a.occ>0 and a.altloc in ('\x00','A')}
assert actual==expected and len(actual)==179
declared={tuple(sorted(tuple(p) for p in x['endpoints'])) for x in item['links']}
native=[]
for connection in structure.connections:
    one,two=connection.partner1,connection.partner2
    if one.chain_name==two.chain_name=='B':
        native.append([[one.res_id.seqid.num,one.atom_name],[two.res_id.seqid.num,two.atom_name]])
assert {tuple(sorted(tuple(p) for p in x)) for x in native}==declared
result={'scope':'Independent atom inventory and explicit covalent links versus deposited 5XCO-derived reference; coordinates not used as input conformer',
        'heavy_atom_identities_and_elements_matched':len(actual),'explicit_links_matched':native,'passed':True,
        'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}
(root/'results/remediation/reference-graph-qc.json').write_text(json.dumps(result,indent=2)+'\n')
print('All 179 atom identities/elements and all three explicit links match 5XCO.')
