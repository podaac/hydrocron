(discharge)=
# River Discharge (SoS)

In addition to the SWOT Level 2 river and lake observations, Hydrocron serves river discharge estimates from the [SWOT Level 4 Sword of Science (SoS) River Discharge Products, Version 3](https://doi.org/10.5067/SWOT-SOS-RD3). These are model-derived discharge (streamflow) estimates produced by SWOT Confluence, matched to the SWOT observation times on each river reach.

## Availability of discharge

SoS discharge is subject to two constraints:

- **Reach only** — discharge fields are added to river reach data, not nodes or lakes.
- **Version 2.0 only** — the SoS V3 products are generated from SWOT L2 RiverSP v2.0 (SWORD v16).

To request discharge, set `feature=Reach` and `collection_name=SWOT_L2_HR_RiverSP_2.0`. If you omit `collection_name` (defaulting to Version D) or request a Version D collection, the discharge fields will not be populated. See the [versioning guide](versioning.md) for more on collection versions.

## Discharge algorithms

The SoS products run several independent discharge algorithms. Each is served through Hydrocron as its own field:
| Field | Algorithm | Description |
|---|---|---|
| `sos_consensus_q` | consensus | Consensus discharge, combining the individual algorithms |
| `sos_hivdi_q` | HiVDI | Hierarchical Variational Discharge Inversion |
| `sos_metroman_q` | MetroMan | Metropolis Manning algorithm |
| `sos_momma_q` | MOMMA | Mean Observed Manning's Metropolis Algorithm |
| `sos_sad_q` | SAD | Slope-Area Discharge |
| `sos_sic4dvar_q` | SIC4DVar | Système Intégré de Calcul 4D Variational |
| `sos_lakeflow_q` | LakeFlow | Discharge derived from connected lake storage change |
| `swot_discharge_reanalysis` | consensus (alias) | Identical data to `sos_consensus_q` (see below) |

All discharge values are in cubic meters per second (m³/s).

:::{note}
**Units are not yet returned for discharge fields.** Unlike `wse` or `area_total`, the discharge fields do not currently have a corresponding `_units` field in the Hydrocron response. This is a known gap that will be addressed in a future release. Until then, treat all `sos_*` discharge values as m³/s.
:::

## Consensus and reanalysis

`swot_discharge_reanalysis` and `sos_consensus_q` return the **exact same data** — the SoS consensus discharge. The two names exist to distinguish the source of the estimate:

- `swot_discharge_reanalysis` / `sos_consensus_q` — the L4 SoS (reanalysis) discharge.
- `dschg_c` / `swot_discharge_nrt` — the L2-provided (near-real-time) discharge that ships in the RiverSP product itself.

The L2 near-real-time discharge (`dschg_*` fields) and the L4 reanalysis discharge (`sos_*` fields) are produced by different processing chains and should not be conflated. Both are available on Version 2.0 reaches.

## Fill values and sparse coverage

Discharge coverage is sparse: at any given observation time, only a subset of the algorithms typically produces a valid estimate. Where an algorithm has no value for a timestep, Hydrocron returns the fill value `-999999999999.0` for that field (the same fill value convention used elsewhere in Hydrocron).

As a result, it is normal to see most discharge fields filled with `-999999999999.0` for many timesteps, with only one or a few algorithms reporting. The `sos_consensus_q` field is generally the most complete, as it combines the individual algorithms.

## Time matching

The SoS products report discharge against their own timestamps. During ingest, each discharge estimate is matched to the closest SWOT observation on the reach (within a time tolerance), so discharge values line up with the `range_start_time` of the corresponding SWOT pass. This means discharge fields appear on the same time series rows as the L2 observations for that reach.

## Field naming conventions

With the implementation of SWOT SoS Discharge data products in Hydrocron, the field names users request through the API are different from the names in the original L4 netCDF, but consistent and corresponding to the respective variable. This was done to help the users discern and track in their request which discharge products they want, given there are several discharge (q) variables in the various groups in the original netCDF, and given the SWOT Level 2 River SP also contains discharge attributes. For example, for L4, consensus_q is renamed sos_consensus_q, hivdi Q is renamed sos_hivdi_q, and so on. This renaming is mapped in the table below. An additional note, that the consensus_q variable from the L4 SoS discharge product can be requested as either sos_consensus_q or swot_discharge_reanalysis, but it is the exact same data. The latter is to discern between the L4-provided discharge and the L2-provided discharge (which has the field names dschg_c or swot_discharge_nrt, again, same data, two difference field names it can be requested by).

```{figure} sos_field_mappings.png
:alt: SoS field mappings
:align: center

SoS discharge field name mappings
```

## Example

For full requests and responses, see:

- [Get time series GeoJSON for river reach with discharge](../examples.md)
- [Get time series CSV for river reach with discharge](../examples.md)
