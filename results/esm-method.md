# ESMC300M masked KRAS profile method

This documents `analysis/modal_esmc.py`. The root agent launched the
configured Modal job and the completed profile is present under
`results/esm/`. The execution used one Modal L4
container with `max_containers=1`,
`min_containers=0`, `timeout=900`, `retries=0`, and `scaledown_window=2`. Raw
logits are returned to the local entrypoint, which writes CPU `.npz`, profile
CSV, substitution CSV, and metadata JSON artifacts.

The entrypoint follows the installed Biohub API: `ESMC(d_model=960,
n_heads=15, n_layers=30)` with `get_esmc_model_tokenizers()` and its `<mask>`
token. The image pins Torch 2.14.0, NumPy 2.5.3, Hugging Face Hub 0.36.2,
Biohub ESM commit `ba4d7124864eed323a93bf3cfefcd958f573b75a`, and Biohub
Transformers commit `ef32577f55da19a4989cd7b22e004dc43a4998cb`.

The invocation passes an immutable Hugging Face `weights_revision` and uses
public-only access (`token=False`), refusing credential fallback.
Official metadata identifies `biohub/esmc-300m-2024-12` as public and ungated,
with current resolved model SHA
`7f10b20ae75017b2dbc884070e03434515709a8d`; its only checkpoint is the legacy
`data/weights/esmc_300m_2024_12_v0.pth`. The function checks gated/private
status before downloading, captures the resolved revision and SHA-256 for every
snapshot file, then loads that `.pth` with `torch.load(..., weights_only=True)`
and strict state-dict validation.

The two FASTA files must each contain one canonical amino-acid sequence of
length 169. The script requires exactly one difference at position 12, WT G
to G12D D. Every residue is masked one at a time with the official tokenizer,
and the full 64-class logits row is retained. The profile reports canonical-20
entropy, native log probability, mean nonnative-minus-native log probability,
and G12D-minus-WT native log probability. The substitution table retains each
canonical nonnative log probability and its difference from the native residue.

At position 12 the masked WT and G12D contexts are identical, so the predicted
logit distributions should match within numerical tolerance. Native
probabilities can nevertheless differ because the WT native token is G and the
G12D native token is D. Metadata records this context QC and checks finite
dimensions at positions 12, 13, and 61. Those positions are QC rows only; the
script performs no hotspot ranking or forced gate.

The command used by the root agent is:

```sh
modal run analysis/modal_esmc.py \
  --wt-fasta target_wt.fasta \
  --g12d-fasta target.fasta \
  --weights-revision 7f10b20ae75017b2dbc884070e03434515709a8d \
  --out-dir results/esm
```

The Modal local-entrypoint and function invocation pattern was checked against
Context7 official Modal documentation (`/websites/modal`). FASTA contents are
read by the local entrypoint and passed as text, so the remote container does
not need a shared filesystem mount. The completed metadata records public-only
access and `credentials_used: false`.

The exact pinned cloud base lock is used, followed by the two Biohub Git pins
with `--no-deps`; CUDA tokens are moved to the model device and a fixed seed of
17 is recorded. The plotting subtask performed no additional deployment or
inference.
