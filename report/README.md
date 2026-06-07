# LaTeX Report

Build the report from this directory:

```bash
rtk env XDG_CACHE_HOME="$PWD/.cache" \
  ./.tools/tectonic reservoir-splatting-report.tex
```

Output:

```text
reservoir-splatting-report.pdf
```

The current workspace uses a user-local Tectonic binary under `.tools/`
because no system TeX engine was installed. The generated PDF is six A4 pages
in a two-column academic layout.

The report uses the verified figures under `report-assets/figures/` and
`disocclusion-results/figures/`. Empirical captions preserve the claim
boundaries documented in
`docs/reproduction/reservoir-splatting-figure-evidence.md`.
