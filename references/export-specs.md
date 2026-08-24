# Export Contract

Export is a capability contract, not a required helper name or copied code block.
The backend adapter may implement it with Matplotlib, R, ComplexHeatmap, SVG, or a
final assembler, provided the export manifest records the evidence.

Required checks for the target output:

- `EXP-001` physical dimensions are verified at final size.
- `EXP-002` the requested format is accepted by the target journal/stage.
- `EXP-003` editable text is preserved where the journal profile requires it.
- `EXP-004` fonts and substitutions are audited where required.
- `EXP-005` raster layers have sufficient effective DPI at final size.
- `EXP-006` vector-capable text and lines remain vector where required.
- `EXP-007` transparency behavior is verified.
- `EXP-008` output color space matches the target contract.
- `EXP-009` every output reopens successfully.
- `EXP-010` the bounding box contains every mark, label, legend, and annotation.
- `EXP-011` unexpected private paths and metadata are absent from delivery files.
- `EXP-012` the export manifest records backend, renderer, fonts, dimensions, and outputs.

The concrete implementation belongs to the selected backend adapter. `save_cns_figure`
and any other legacy helper may remain as a local convenience, but its name is not a
production gate and it must not be copied verbatim into every script.
