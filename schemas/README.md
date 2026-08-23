# Canonical artifact schemas

Route artifacts use explicit `schema_version` fields. `contracts.schema.json`
defines the transport envelope (`contract_name`, `schema_version`, and a JSON
object payload); the Python dataclasses enforce the per-contract fields and
reject unknown keys. Adapters ship this directory with the skill bundle.
`reference-dna.schema.json` defines the source-aware visual evidence contract;
its `2.0` is the current DNA schema, not a parallel runtime implementation.
