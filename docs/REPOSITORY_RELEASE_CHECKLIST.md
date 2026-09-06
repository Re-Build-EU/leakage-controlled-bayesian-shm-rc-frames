# Re-BUILD-EU GitHub and Zenodo release checklist

1. Create a dedicated directory in the public Re-BUILD-EU GitHub repository, for example `research-outputs/SHM_RC_Frames/`.
2. Copy the **contents** of this package into that directory. Keep the folder structure unchanged.
3. Run `python scripts/00_verify_package.py` from the package root and confirm `PACKAGE VALIDATION: PASS`.
4. Run `python scripts/01_dataset_summary.py`, `02_reproduce_tables.py`, and `03_reproduce_figures.py` once on the public clone.
5. Confirm that no publisher PDFs, manuscript-review files, private paths, credentials, or temporary analysis files are present.
6. Confirm that the repository is publicly accessible in a private/incognito browser window.
7. Commit with a clear release message, e.g. `Release SHM RC-frame reproducibility package v1.0.0`.
8. Create a GitHub Release tagged `v1.0.0`.
9. Enable the GitHub-Zenodo integration for the Re-BUILD-EU repository and archive the release.
10. Copy the Zenodo DOI into `repository_metadata.json`, `docs/DATA_AVAILABILITY_STATEMENT.md`, and the journal manuscript.
11. If a DOI-containing metadata update requires a second tag, create `v1.0.1` containing metadata-only changes and keep `v1.0.0` permanently archived.
12. Cite both the article and the repository release in future reuse.
