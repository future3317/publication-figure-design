# Figure Family Champion Board

The champion board is the quality-improvement ledger used after the compiler
architecture is frozen. It does not replace the scientific or export gates and it
does not promote a reference from metadata alone.

## Candidate loop

For a representative task in a figure family:

1. Run publication mode and render the structure-first, style-first, and balanced
   candidates at final physical size.
2. Inspect the three candidates blind to their generation order. Preserve the
   before/reference/after evidence and the final QA artifacts.
3. Record exactly one `preferred` and one `rejected` candidate with at least one
   controlled `reason_code` using `scripts/record_preference.py`.
4. Update the family row in `assets/reference-benchmarks/champion_board.json` only
   when the challenger wins pairwise review and has scientific, L0, L1, L2, and L3
   evidence.
5. Run `scripts/champion_board.py` and the normal release gate. A family with fewer
   than five reviewed tasks stays `needs_evidence`; it is not treated as a champion.

Example:

```powershell
& "D:\Anaconda\envs\piepaper\python.exe" scripts/record_preference.py candidate-a candidate-b left `
  --task-id grouped_bar_01 `
  --figure-family comparison_effect `
  --reason-code hierarchy `
  --reason-code whitespace `
  --reviewer human
& "D:\Anaconda\envs\piepaper\python.exe" scripts/champion_board.py --output tmp/champion-board.json
```

The preference record keeps `left/right/winner` for benchmark readers and also writes
the canonical `preferred/rejected/reason_codes` fields. Reason codes should describe a
visible cause (for example `hierarchy`, `spacing`, `typography`, `palette_discipline`,
`annotation_clearance`, `data_clarity`, or `scientific_correctness`), not a vague score.

## Board fields

Each family records:

- `champion`, `challenger`, and `last_release` for generated tasks;
- optional `reference_upper_bound` for a strong visual reference that is not a generated
  champion;
- human preference win rate and reason-code counts;
- scientific pass, L0/L1/L2/L3, and repair iterations;
- reference coverage, quality, diversity, and their product;
- explicit gaps for annotation grammar, topology, dense/sparse density, journal/profile,
  palette roles, direct-label/legendless layouts, asymmetric heroes, and mixed
  image-plus-quantitative panels.

The board's KPI is `coverage × quality × diversity`, not reference count. The report is
diagnostic: it identifies where to add a high-value reference or a pairwise task, while
the production recommendation pool still follows the normal quarantine and benchmark
gates.
