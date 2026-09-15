# Boltz-2 representation audit: capped KRpep-2d and backbone-cyclic variants

Current status: the pinned runtime and exact CCD bundle were obtained and both full controls passed the official parser. Six predictions completed; the control separation gate FAILED. Output terminal-cap geometry is also distorted. See `CALIBRATION_REPORT.md`. The sections below preserve the earlier pre-inference representation audit and its then-open questions; they are historical, not current execution status.

## Sources inspected

- Official repository: [`jwohlwend/boltz`](https://github.com/jwohlwend/boltz), audited at commit [`b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc`](https://github.com/jwohlwend/boltz/tree/b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc).
- Official input documentation at that commit: [`docs/prediction.md`](https://github.com/jwohlwend/boltz/blob/b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc/docs/prediction.md), especially lines 66–94 and 103–104. The same documentation says YAML supports modified residues and covalent bonds while deprecated FASTA does not (lines 299–312).
- Parser: [`src/boltz/data/parse/schema.py`](https://github.com/jwohlwend/boltz/blob/b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc/src/boltz/data/parse/schema.py), lines 1018–1034, 1141–1182, 1184–1234, 1511–1526, and 1755–1759.
- Native observed structure already in this project: [`results/target/5xco-reference.cif`](5xco-reference.cif). Its `_chem_comp` table contains `ACE` and `NH2`; `_struct_conn` records `ACE C`–peptide residue 1 `N`, peptide residue 19 `C`–`NH2 N`, and the Cys5–Cys15 disulfide.

## What the parser actually supports

The YAML `sequences` schema accepts protein polymers with a sequence, and ligand entities with exactly one of `ccd` or `smiles` (docs lines 68–71; parser lines 1018–1034). A polymer `modifications` entry is 1-indexed and replaces the sequence token with the supplied CCD code (parser lines 1158–1170). The official docs qualify this as CCD based and do not define an ACE/NH2 shortcut or a terminal-cap field.

The `cyclic` flag applies to a polymer, not a ligand (docs line 83; parser lines 1171–1181 and the ligand assertion at lines 1232–1234). In the parser, `cyclic: true` sets `cyclic_period` to the full sequence length (lines 914–925). Therefore it describes a cycle of the entire polymer chain. It is not a field for an internal 12–16 closure.

The `bond` constraint accepts two atom endpoints `[CHAIN_ID, RES_IDX, ATOM_NAME]` and resolves them through the atom map (parser lines 1516–1526). For Boltz-2, those connections are appended as covalent bonds in the parsed structure (lines 1755–1759), and the tokenizer carries connection bonds into token bonds (source `src/boltz/data/tokenize/boltz.py`, lines 194–205). The docs restrict this feature to CCD ligands and canonical residues (line 90), which covers ACE/NH2 as CCD ligands bonded to canonical peptide atoms and an explicit Cys5–Cys15 bond.

Boltz-2 affinity properties are a separate limitation: the docs require the `properties.affinity.binder` to be one ligand chain and state that affinity currently supports a small-molecule ligand, not a protein/DNA/RNA binder (docs lines 103–104; parser lines 1045–1077). A capped peptide represented as a protein chain therefore cannot be silently treated as a supported affinity ligand.

## Minimal chemically faithful YAML shape

The following is a schema shape, not a validated runnable input. `ACE` and `NH2` are used only because they are observed component identifiers in 5XCO and must still be confirmed in the exact Boltz CCD bundle before execution:

```yaml
version: 1
sequences:
  - protein:
      id: B
      sequence: RRRRCPLYISYDPVCRRRR
      msa: empty
      cyclic: false
  - ligand:
      id: C
      ccd: ACE
  - ligand:
      id: D
      ccd: NH2
constraints:
  - bond:
      atom1: [C, 1, C]
      atom2: [B, 1, N]
  - bond:
      atom1: [B, 5, SG]
      atom2: [B, 15, SG]
  - bond:
      atom1: [B, 19, C]
      atom2: [D, 1, N]
```

This encodes the observed 19-residue sequence, N-acetyl and C-amide caps as separate CCD entities, and the observed Cys5–Cys15 disulfide. The native 5XCO structure confirms the endpoint atom names and connectivity; it does not prove that the campaign's CCD bundle contains both components.

For a backbone-cyclic design containing **12 to 16 residues in total**, use its complete sequence with `cyclic: true`. Do not add the KRpep-2d-specific caps or disulfide to that chemically different design. The phrase 12–16 in the specification is a length range, not endpoints of an internal closure. The earlier draft's internal-bond interpretation was incorrect and has been removed before any input dispatch.

## Historical pre-inference blockers (subsequently resolved at parser level)

The representation has a documented parser path, but the exact comparison requested is not yet validated for two reasons:

1. The local workspace has no installed `boltz` package or campaign CCD bundle. The repository parser loads CCD molecules from its runtime component store (`src/boltz/data/mol.py`, `load_molecules`); a native RCSB component ID alone is insufficient to claim the local runtime will resolve it.
2. Separate ACE and NH2 chains add two nonpolymer chains and explicit inter-chain connections. The inspected official sources show that these connections are preserved in structure/token features, but do not promise that adding cap chains leaves pair-chain ipTM unchanged. A score comparison must therefore use one validated representation for every condition and inspect the resulting chain/interface bookkeeping.

The honest next step is to validate the above YAML with the pinned Boltz-2 runtime and its CCD bundle, then inspect parsed chains, connection bonds, cyclic period, and score metadata before any campaign inference. Until that is done, no positive control or cyclic design score should be reported.
