# Privacy and Provenance Boundary

Keep two reporting layers:

## Internal audit record

Record exact source paths, asset filenames, reference IDs, template IDs, copied-script provenance, field mappings, exclusions, runtime commands, and output paths in source headers or machine-readable QA artifacts. This supports reproducibility and debugging.

## User-facing summary

Report the semantic source and decision—for example, “structurally adapted from the selected grouped-distribution reference”—without exposing private directory names, local usernames, unpublished filenames, template IDs, or temporary working paths unless the user explicitly asks for them.

Never put secrets, credentials, hidden metadata, or unrelated local paths in a figure, legend, report, or exported file. Preserve required scientific source-data traceability without leaking unrelated filesystem provenance.
