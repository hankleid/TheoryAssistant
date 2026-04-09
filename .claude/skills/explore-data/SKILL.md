---
name: explore-data
description: "Explore data files in the project: discover formats, shapes, axes, and anomalies to ground subsequent analysis"
allowed-tools: Read, Bash, Glob, Grep
---
# Explore Data

Run a comprehensive exploration of the experimental data files available in this project to ground any subsequent analysis in actual data characteristics.

## Step 1 — Discover data files

Use Glob to find all data files (`.json`, `.csv`, `.npy`, `.hdf5`, `.mat`, `.txt`, etc.) and any existing loader scripts (e.g. `tools/data_io.py`, `tools/load_*.py`). List what you find.

## Step 2 — Run existing loaders (if present)

If a loader script exists with a `__main__` block, run it:
```bash
conda run -n 3p12 python tools/data_io.py   # adjust env/path as needed
```
Capture stdout. If no loader exists, load files directly using Python (`json.load`, `numpy.load`, `pandas.read_csv`, etc.) via Bash.

## Step 3 — For each dataset, report

- **Format & shape**: file format, array/table dimensions, dtype
- **Axes**: what each dimension represents (time, space, wavelength, parameter sweep, …), units if discoverable
- **Value ranges**: min, max, median for the primary signal arrays
- **Sampling**: step sizes, bin widths, or sweep ranges along each axis
- **Structure**: nested keys (JSON), column names (CSV), dataset names (HDF5)

## Step 4 — Cross-checks and anomalies

- Are sweep dimensions consistent across datasets that should share an axis?
- Any NaNs, negative counts where unphysical, unexpected shapes, or truncated files?
- Rough signal quality: dynamic range, noise floor, obvious outliers

## Outputs

Print a readable structured summary to stdout. No files written. The summary should give a reader enough information to design an analysis plan without opening any data file themselves.
