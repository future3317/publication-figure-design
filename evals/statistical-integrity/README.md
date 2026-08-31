# Statistical integrity eval suite

Tests preservation of paired identity, uncertainty semantics, observation units,
and visibility of small-sample distributions.

## Tasks

- `lost_pair_identity`: paired observations must not collapse into independent bars.
- `mean_bar_hides_distribution`: small-sample continuous data needs distribution marks.
- `wrong_errorbar_semantics`: SD vs SEM vs CI must be declared correctly.

See `tasks.jsonl`.
