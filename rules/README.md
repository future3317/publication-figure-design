# Rule model

Rules are the machine-readable source of truth for design decisions. Every rule
has an ID, scope, severity, statement, verification procedure, and (for externally
grounded rules) a source entry in `sources/registry.yaml`.

## Precedence

`G0 scientific integrity > G1 accessibility/legibility > J journal hard requirements > explicit user requirements > F family rules > H house defaults > B backend defaults`.

When two non-overridable rules conflict, the runtime blocks and reports the conflict;
it does not silently let a later-loaded document win. Benchmark and champion data are
evaluation policy, not design rules.
