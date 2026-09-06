# Simulation dataset

`fem_dataset_528.csv` is the canonical simulation dataset used for all analyses in this repository.

It contains 528 unique nonlinear pushover cases spanning eight geometry families: 2S2B, 3S2B, 3S3B, 4S3B, L2S2B, L3S2B, L2S2B-stilt, and L3S2B-stilt. The population contains 288 full-scale regular cases, 144 laboratory-scale regular cases, and 96 laboratory-scale stilted cases.

The maximum interstory drift ratio is evaluated from the relative displacement between the end nodes of each column divided by that column's actual vertical height, maximized over all columns and converged pushover steps. This definition is particularly important for stilted frames.

Of the 528 analyses, 511 reached the prescribed target displacement. For the remaining 17 cases, the response variables represent the final available converged structural state. These cases are retained to preserve the complete controlled simulation population; `ConvergedFully` explicitly records this status.

See `data_dictionary.csv` and `docs/METHODS_AND_REPRODUCTION.md` for definitions and modelling details.
