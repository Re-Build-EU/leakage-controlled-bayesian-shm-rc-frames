# Manuscript result-to-file map

| Manuscript item | Repository source | Reproduction utility |
|---|---|---|
| Target distributions / target definitions | `data/simulation/fem_dataset_528.csv` | `scripts/01_dataset_summary.py` |
| Fig. 5 target correlations | `results/figure_data/fig5_target_correlations.csv` | `scripts/03_reproduce_figures.py` |
| Fig. 6 member-response stratification | `data/simulation/fem_dataset_528.csv`; `results/mechanism/member_response_statistics.csv` | `scripts/03_reproduce_figures.py` |
| Leakage table / leakage scores | `results/repeated_cv/leakage_effect.csv` | `scripts/02_reproduce_tables.py`, `03_reproduce_figures.py` |
| Strict same-scalar comparison | `results/sensitivity/strict_leakage/` | `scripts/02_reproduce_tables.py` |
| Leakage-controlled model comparison | `results/repeated_cv/repeated_summary.csv`; `results/figure_data/fig9_model_comparison.csv` | `scripts/02_reproduce_tables.py`, `03_reproduce_figures.py` |
| Bayesian topology sensitivity | `results/sensitivity/topology/` | `scripts/02_reproduce_tables.py` |
| Posterior calibration / reliability | `results/calibration/` | `scripts/02_reproduce_tables.py`, `03_reproduce_figures.py` |
| Leave-one-geometry-out validation | `results/geometry_transfer/` | `scripts/02_reproduce_tables.py` |
| Experimental posterior probabilities | `data/experimental/` | `scripts/02_reproduce_tables.py`, `03_reproduce_figures.py` |
| Threshold sensitivity | `results/sensitivity/thresholds/` | `scripts/02_reproduce_tables.py` |
| Nonlinear-region-length sensitivity | `results/sensitivity/hinge_length/` | `scripts/02_reproduce_tables.py` |
