# Final figure revision requests, 2026-06-10

This note records requested changes and interpretation questions for the current
RCCN final figures A-E.

## Fig A

- Redraw Fig A.
- Replace the y-axis with `1 - CDF`, the fraction of cells that have not yet
  resumed growth.
- Use the paper-style lag-time definition: lag time is the time when
  magnetization `M` returns to `0`; cells with `M = 0` are treated as recovered
  / resumed-growth cells.
- Compute `1 - CDF` from the fraction of unrecovered cells over recovery time.
- Split Fig A into two subplots:
  - semi-log scale, with log scaling on the y-axis;
  - log-log scale, with log scaling on both x- and y-axes.

## Fig B

- Change the three recovery-time colors to:
  - `RGB(255, 183, 3)`
  - `RGB(90, 24, 154)`
  - `RGB(230, 57, 20)`
- Add a simple auxiliary trajectory summary:
  - for each `Tw` panel and each recovery snapshot time, compute the UMAP
    centroid across cells;
  - connect the centroids in recovery-time order, `0 -> 20 -> 120 min`, using
    arrows;
  - use this only as a visual guide for the average state-space displacement,
    while keeping the individual cell scatter points visible.

## Fig C

- Answer how the three spin clusters are defined.
- Answer how to read the right subplot:
  - clarify whether it is showing three points, 95% quantiles, medians, or a
    distribution.
- Change cluster colors to:
  - cluster 0: `RGB(65, 152, 172)`
  - cluster 1: `RGB(123, 192, 205)`
  - cluster 2: `RGB(219, 203, 146)`
- Move the left subplot legend outside the plotting area if possible.

## Fig D

- Answer how the y-axis is calculated.
- Clarify whether the y-axis is a relative proportion or an absolute
  magnetization value.
- If it is an absolute value, note that smaller values for short loops may be
  expected and should not be over-interpreted as a relative depletion.
- Answer which `Tw` / release-state subset is used for this figure.
- Redraw Fig D as a set of related plots:
  - keep the current mixed-all-`Tw` version;
  - additionally generate one same-format plot for each `Tw` separately:
    `Tw = 0, 195, 488, 1346, 1500`;
  - use the same y-axis definition and cycle-group colors across all versions
    so the mixed and per-`Tw` plots can be compared directly.

## Fig E

- Change colors to:
  - normal: `RGB(22, 50, 115)`
  - presister-like: `RGB(250, 81, 124)`
- Add marginal distribution plots to the PCA panel:
  - show the marginal distributions of the normal and presister-like groups
    along PC1 and PC2;
  - keep the distributions visually tied to the PCA scatter colors.
- Answer what distinguishes different cells in RCCN PCA and UMAP.
- Answer whether weak separation could arise because the distinguishable
  dimensions in this RCCN feature representation are lower than in single-cell
  experimental data.
