# Complete reproduction tutorial

## 1. Download and verify

Clone or download the Re-BUILD-EU repository release, then enter this package directory.

```bash
python scripts/00_verify_package.py
```

A successful run prints `PACKAGE VALIDATION: PASS`. The script checks dataset integrity, target class counts, key model results, calibration values, geometry-transfer results, sensitivity analyses, and experimental posterior probabilities against the canonical archived output files.

## 2. Create the Python environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows**
```powershell
.venv\Scripts\activate
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Install the lightweight reproduction dependencies:

```bash
pip install -r requirements.txt
```

For protocol-level Bayesian/ML recomputation:

```bash
pip install -r requirements-model.txt
```

## 3. Inspect the simulation data

```bash
python scripts/01_dataset_summary.py
```

This writes dataset integrity and target-class summaries to `generated/tables/`.

The canonical simulation file contains 528 unique cases and 41 fields. The final target distributions are:

- DamageState: 51 none, 85 minor, 97 moderate, 295 severe;
- StiffnessLoss: 74 low, 166 medium, 288 high;
- ResidualCapacity: 141 failed, 387 retained.

The convergence flag records 511 fully converged cases and 17 cases for which terminal response quantities correspond to the last converged state.

## 4. Regenerate manuscript tables

```bash
python scripts/02_reproduce_tables.py
```

The script reads the canonical archived result files and writes compact manuscript-ready CSVs to `generated/tables/`.

## 5. Regenerate principal figures

```bash
python scripts/03_reproduce_figures.py
```

The generated figures are written to `figures/`:

- `fig5_target_correlations.png`
- `fig6_member_response_stratification.png`
- `fig7_bn_leakage_effect.png`
- `fig8_leakage_scores.png`
- `fig9_model_comparison.png`
- `fig10_posterior_calibration.png`
- `fig15_experimental_posteriors.png`

## 6. Audit the repeated cross-validation result

Open `results/repeated_cv/repeated_summary.csv`. Filter `Regime == controlled` and `Model == Bayesian network`. The expected macro F1 values are:

- DamageState: 0.626286
- StiffnessLoss: 0.741342
- ResidualCapacity: 0.645458

`leakage_effect.csv` records both full-evidence and leakage-controlled results and the fractional leakage score.

## 7. Audit posterior calibration

`results/calibration/bn_oof_posteriors.csv` contains all pooled out-of-fold Bayesian posterior vectors. There are 1,584 out-of-fold predictions for each target (528 cases × 3 repetitions).

`posterior_calibration.csv` contains the reported accuracy, mean confidence, multiclass Brier score, and ECE.

## 8. Audit geometry transfer

`results/geometry_transfer/logo_by_geometry.csv` reports accuracy, macro F1, and mean confidence separately for every held-out geometry family. `logo_summary.csv` gives the mean and standard deviation across the eight held-out configurations.

## 9. Audit same-scalar and topology sensitivity

The `results/sensitivity/strict_leakage/` directory compares inference-only withholding with complete same-scalar node removal and refitting.

The `results/sensitivity/topology/` directory contains results for the adopted network and three engineering-motivated topology alternatives. Prediction-level files are included so changes in individual posterior decisions can be audited, not only aggregate scores.

## 10. Audit threshold and hinge-length sensitivity

`results/sensitivity/thresholds/` contains label agreement, class-balance, and transition tables for ±0.05 shifts in stiffness-loss and residual-capacity thresholds.

`results/sensitivity/hinge_length/` contains the three-frame nonlinear-region-length check for Lp/Lm = 0.08, 0.10, and 0.12. The maximum changes relative to 0.10 are approximately 1.55% in peak base shear, 4.14% in true maximum interstory drift, 0.74% in stiffness loss, and 3.66% in postpeak strength retention; target classifications remain unchanged.

## 11. Audit the experimental demonstration

`data/experimental/experimental_evidence_and_posteriors.csv` is the canonical processed experimental input/output table. Missing source quantities remain unobserved. The expected coarse posterior probabilities are:

| Specimen | P(significant damage) | P(substantial stiffness loss) |
|---|---:|---:|
| EF | 0.943 | 0.996 |
| RF | 0.888 | 0.995 |
| DJ-1 | 0.897 | 0.955 |
| DJ-2 | 0.897 | 0.955 |

See `docs/DATA_PROVENANCE.md` before using these processed values.

## 12. Protocol-level model implementation

`scripts/04_reference_model_protocol.py` documents and implements the final evidence construction, expert-specified Bayesian topology, same-scalar withholding rule, benchmark model configuration, and foldwise preprocessing logic. It is provided for methodological reproduction. The archived fold-level output files under `results/` remain the canonical numerical record for the article because numerical libraries and Bayesian-inference implementations can exhibit version-dependent differences in tie handling and low-probability states.

For an end-to-end recomputation of repeated validation, geometry transfer, strict node removal, and topology sensitivity, run:

```bash
python scripts/05_recompute_analysis.py --mode all
```

This writes a separate `recomputed/` directory and never overwrites the canonical archived result files.

## 13. Prepare the public GitHub release

Follow `docs/REPOSITORY_RELEASE_CHECKLIST.md`. The recommended release tag is `v1.0.0`. Connect the Re-BUILD-EU GitHub repository to Zenodo, archive the release, and then replace the repository/DOI placeholders in `repository_metadata.json` and `docs/DATA_AVAILABILITY_STATEMENT.md`.
