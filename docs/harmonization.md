# MODIS and VIIRS Data Harmonization Methodology

## 1. Overview

This project aims to develop a harmonized active-fire dataset by integrating historical observations from the Moderate Resolution Imaging Spectroradiometer (MODIS) and the Visible Infrared Imaging Radiometer Suite (VIIRS).

MODIS, aboard the Terra and Aqua satellites, provides a long-term record of global fire activity. VIIRS, aboard the NOAA-20 satellite, provides finer spatial observations and improved sensitivity to smaller and lower-intensity fires. However, differences in sensor characteristics, spatial resolution, observation geometry, spectral response, and detection algorithms can introduce inconsistencies when combining their observations directly.

The objective of this harmonization is to establish a consistent fire radiative power (FRP) record while retaining the spatial and temporal information required for long-term fire activity analysis, including trend detection, anomaly identification, and the development of fire activity calendars.

The output is designed around the MODIS footprint as the reference spatial unit. VIIRS observations are matched and aggregated to this reference footprint, and the resulting FRP estimates are integrated using an empirical calibration and quality-prioritized fusion approach.

The methodology is organized into two main components:

1. **Non-FRP feature standardization:** ensuring consistent data representation, quality filtering, spatial referencing, and temporal matching.
2. **FRP harmonization:** correcting sensor-specific FRP differences through duplicate correction, spatial aggregation, statistical screening, empirical calibration, and sensor fusion.

---

## 2. Features Needed to Be Harmonized

Not every field should be converted into a common numerical scale. Some features require standardization, some are used for matching or quality control, and others should remain sensor-specific because they represent different spectral measurements.

| Feature | Definition | Why it needs to be harmonized or standardized | Treatment |
|---|---|---|---|
| Latitude and longitude | Geographic coordinates of the detected fire pixel, expressed in degrees | MODIS and VIIRS detect fires at different spatial resolutions. A common spatial reference is required to associate detections with the same observation area. | Retain MODIS coordinates as the reference location of each output footprint. |
| Acquisition date and time | Date and UTC time at which the satellite observes the fire | Observations from the two sensors may occur at different times. Temporal alignment is necessary to reduce mismatches caused by changing fire activity. | Parse into a common UTC datetime and apply a maximum temporal difference of 5 minutes. |
| Scan | Approximate pixel dimension in the along-scan direction, in kilometres | Footprint dimensions vary with sensor geometry and viewing position. This information is required to reconstruct approximate pixel footprints. | Retain sensor-specific values and use them for footprint reconstruction. |
| Track | Approximate pixel dimension in the along-track direction, in kilometres | Footprint dimensions influence spatial overlap and the estimated MODIS viewing zenith angle (VZA). | Retain sensor-specific values; use MODIS track to estimate VZA. |
| Brightness | MODIS fire-pixel brightness temperature, generally associated with the MODIS 4 µm channel | Brightness measurements help characterize thermal anomalies, but the MODIS and VIIRS channels have different spectral response functions. | Retain MODIS brightness and VIIRS brightness temperatures as separate sensor-specific variables. |
| Brightness temperature T31 | MODIS brightness temperature from the approximately 11 µm thermal infrared channel | Provides additional thermal information and may support subsequent fire characterization. There is no directly equivalent field in the supplied VIIRS dataset. | Retain as a MODIS-specific feature. |
| Brightness temperature I4 (TI4) | VIIRS brightness temperature from the I4 channel, approximately 3.7–4.0 µm | Provides thermal information from the VIIRS fire pixel. It is spectrally related to, but not directly interchangeable with, MODIS brightness. | Retain separately and aggregate the contributing VIIRS values within each matched MODIS footprint. |
| Brightness temperature I5 (TI5) | VIIRS brightness temperature from the I5 channel, approximately 11–12 µm | Provides additional thermal information from VIIRS, but its spectral response differs from the MODIS T31 channel. | Retain separately and aggregate the contributing VIIRS values within each matched MODIS footprint. |
| Confidence | Sensor-specific assessment of the reliability of a detected fire pixel | MODIS and VIIRS use different confidence representations. A common ordinal representation is needed for quality-prioritized fusion. | Convert to low, nominal, and high classes, represented by ranks 1, 2, and 3. |
| Fire type | Classification of the detected thermal anomaly | The datasets may include vegetation fires, volcanoes, gas flares, and other thermal anomalies. Non-wildland detections can introduce unwanted variation into a wildfire analysis. | Retain only `type = 0`, representing presumed vegetation fires. |
| Day/night | Indicates whether the observation was acquired during daytime or nighttime | Daytime and nighttime observations can have different detection characteristics and thermal backgrounds. | Standardize representation and retain the MODIS value as the output reference, while preserving VIIRS metadata where required. |
| Satellite and instrument | Identifies the satellite platform and observing instrument | The records originate from different platforms and instruments, which must remain identifiable for quality control and traceability. | Retain the original sensor and satellite identifiers. |
| Version | Identifies the product collection or processing version | Different product versions may incorporate different processing algorithms or input data. Version information is needed for reproducibility and quality assessment. | Retain the original version information. |
| Fire Radiative Power (FRP) | Radiative energy released by an active fire, generally expressed in megawatts (MW) | FRP is affected by sensor resolution, observation geometry, detection sensitivity, and retrieval differences. Directly combining the original values may introduce systematic inconsistencies. | Apply the FRP harmonization methodology described in Section 4. |

### Important distinction concerning brightness temperatures

MODIS brightness, MODIS T31, VIIRS TI4, and VIIRS TI5 are not identical measurements. Even when two channels cover similar spectral regions, differences in their spectral response, calibration, spatial resolution, and retrieval characteristics mean that their numerical values should not automatically be treated as equivalent.

Consequently, this methodology does not apply a direct numerical conversion between the brightness-temperature fields. Instead, it preserves the original sensor-specific measurements and aggregates VIIRS brightness temperatures to the MODIS spatial reference footprint.

FRP is treated differently because the main objective is to establish an empirically consistent quantitative record across the two sensors.

---

## 3. Methods

### 3.1. Standardization and harmonization of non-FRP features

#### 3.1.1. Data quality filtering

Before matching the two datasets, both MODIS and VIIRS records undergo independent quality filtering.

The following conditions are applied:

- Remove records with missing or invalid geographic coordinates.
- Remove records with missing acquisition dates or times.
- Remove records with missing, zero, or negative FRP values.
- Remove records with invalid or non-positive scan and track dimensions.
- Retain only detections classified as presumed vegetation fires (`type = 0`).
- Remove records with unrecognized confidence classifications because they cannot be reliably prioritized during fusion.

This filtering ensures that subsequent spatial matching, temporal alignment, and FRP calibration use valid fire observations.

#### 3.1.2. Temporal standardization

The acquisition date and time fields from both datasets are converted into a common UTC datetime representation.

The temporal difference between a MODIS observation and a VIIRS observation is calculated as:

$$
\Delta t_{ij} = |t_{\mathrm{VIIRS},j}-t_{\mathrm{MODIS},i}|
$$

A pair is considered temporally eligible when:

$$
\Delta t_{ij} \leq 5\text{ minutes}
$$

This threshold is used to identify near-synchronous observations while reducing the possibility that changes in fire activity between separate satellite observations will be interpreted as sensor-related differences.

The original acquisition date and time fields are retained for traceability.

#### 3.1.3. Spatial footprint reconstruction

Because MODIS and VIIRS have different spatial resolutions, their detected fire pixels cannot be matched reliably using geographic centre coordinates alone.

Approximate pixel footprints are therefore reconstructed using the reported pixel centre coordinates and scan and track dimensions.

For each detection, the footprint is represented by an axis-aligned rectangle:

$$
P_i = [x_{\min},x_{\max}]\times[y_{\min},y_{\max}]
$$

where the horizontal and vertical dimensions are estimated from scan and track:

$$
\Delta x = \frac{\mathrm{scan}}{111.32\cos(\phi)}
$$

$$
\Delta y = \frac{\mathrm{track}}{111.32}
$$

where:

- \(\phi\) is the pixel-centre latitude;
- scan represents the approximate east-west pixel dimension in kilometres;
- track represents the approximate north-south pixel dimension in kilometres;
- 111.32 is the approximate number of kilometres per degree of latitude.

The resulting geometry is an approximation based on FIRMS pixel dimensions. It does not represent the exact geolocated corners of the original satellite pixels.

The same documented geometry method is applied consistently during duplicate correction and cross-sensor spatial matching.

#### 3.1.4. Sensor-specific duplicate correction

Duplicate detections can occur when adjacent scan observations overlap or when the same fire is reported repeatedly within a short time interval.

Duplicate correction is performed independently for MODIS and VIIRS before cross-sensor matching.

Two detections are considered duplicates when both conditions are satisfied:

1. Their absolute acquisition-time difference is less than 8 seconds:

$$
|t_i-t_j| < 8\text{ seconds}
$$

2. Their reconstructed pixel footprints overlap by more than 30%:

$$
O_{ij} =
\frac{\operatorname{Area}(P_i\cap P_j)}
{\min(\operatorname{Area}(P_i),\operatorname{Area}(P_j))}
> 0.30
$$

This overlap metric measures the intersection relative to the smaller footprint. It allows a smaller footprint contained within a larger footprint to be treated as substantially overlapping.

For each duplicate group:

- Retain the detection with the highest confidence rank.
- If multiple detections have the same confidence rank, retain the earliest detection.
- Replace the retained detection's FRP with the arithmetic mean FRP of all detections in the duplicate group.

The group-averaged FRP is:

$$
FRP_{\mathrm{duplicate}} =
\frac{1}{n}\sum_{i=1}^{n}FRP_i
$$

This reduces repeated observations without allowing duplicate detections to contribute multiple times to subsequent spatial aggregation.

#### 3.1.5. Confidence standardization

MODIS and VIIRS use different confidence representations.

For the purpose of quality-prioritized fusion, the confidence information is converted into a common ordinal classification:

| Standardized confidence class | Confidence rank | MODIS confidence | VIIRS confidence |
|---|---:|---|---|
| Low | 1 | 0–29 | L |
| Nominal | 2 | 30–79 | N |
| High | 3 | 80–100 | H |

This mapping provides a common ranking system for comparing the relative confidence classes of the two sensors.

The ranks are ordinal quality categories, not calibrated probabilities. A VIIRS high-confidence detection and a MODIS high-confidence detection are not necessarily associated with identical statistical probabilities of correctness.

The standardized ranks are therefore used only as a relative priority rule during fusion.

#### 3.1.6. Brightness-temperature handling

Brightness-related variables are retained according to their original sensor definitions.

For each matched MODIS footprint:

- MODIS brightness and T31 remain associated with the original MODIS observation.
- VIIRS TI4 and TI5 are aggregated from the VIIRS detections contributing to that MODIS footprint.
- The VIIRS brightness-temperature aggregation uses the arithmetic mean.

For a MODIS footprint containing \(n\) contributing VIIRS detections:

$$
\overline{T}_{I4} =
\frac{1}{n}\sum_{j=1}^{n}T_{I4,j}
$$

$$
\overline{T}_{I5} =
\frac{1}{n}\sum_{j=1}^{n}T_{I5,j}
$$

These aggregated values represent the mean brightness temperatures of the contributing VIIRS fire detections, rather than the mean temperature of every pixel within the MODIS footprint.

No direct brightness-temperature conversion is applied because the corresponding spectral channels are not identical.

---

### 3.2. FRP harmonization

FRP is the primary quantitative variable being harmonized. The methodology follows a correction-before-fusion approach: duplicate correction and spatial aggregation are performed before empirical calibration, and the resulting estimates are integrated using confidence-based prioritization.

#### Step 1. Independent sensor-specific preprocessing

MODIS and VIIRS are independently filtered and deduplicated using the procedures described in Sections 3.1.1 and 3.1.4.

This prevents repeated observations within either sensor from artificially increasing the aggregated FRP.

The two sensors are not deduplicated against each other at this stage.

#### Step 2. Spatial and temporal matching

The reconstructed VIIRS footprints are spatially indexed to identify potential contributors to each MODIS footprint.

For a MODIS footprint \(P_i\), a VIIRS detection \(j\) is eligible for aggregation when:

\[
\operatorname{Centre}(P_j)\in P_i
\]

and:

\[
|t_j-t_i|\leq 5\text{ minutes}
\]

The spatial condition requires the centre of the VIIRS footprint to fall inside or on the boundary of the MODIS footprint.

The temporal condition ensures that the contributing VIIRS observation is sufficiently close to the MODIS acquisition time.

Only MODIS footprints with at least one qualifying VIIRS detection are retained in the harmonized dataset.

#### Step 3. VIIRS FRP aggregation

Because VIIRS has finer spatial resolution than MODIS, multiple VIIRS fire detections may fall within one MODIS footprint.

Their FRP values are aggregated by summation:

\[
FRP_{\mathrm{VIIRS,aggregated},i}
=
\sum_{j=1}^{n_i} FRP_{\mathrm{VIIRS},j}
\]

where \(n_i\) represents the number of VIIRS detections whose centres fall inside the MODIS footprint and satisfy the temporal matching condition.

This produces a VIIRS-derived FRP estimate corresponding to the spatial support of the MODIS footprint.

The aggregated VIIRS FRP is used directly:

\[
FRP_{\mathrm{VIIRS,reference}}
=
FRP_{\mathrm{VIIRS,aggregated}}
\]

No area-based cloud correction is applied in this implementation because the required clear-sky and cloud-covered area information is not available in the selected input feature set.

Consequently, the VIIRS reference FRP should be interpreted as an uncorrected spatial aggregate rather than a cloud-corrected estimate.

#### Step 4. Anomalous matched-sample screening

Some matched observations may contain unusually large FRP differences caused by residual duplicate detections, temporal variation, spatial mismatch, or sensor-specific retrieval effects.

To reduce the influence of extreme observations during calibration, the logarithmic FRP ratio is calculated for each matched footprint:

\[
q_i =
\ln\left(
\frac{FRP_{\mathrm{VIIRS,aggregated},i}}
{FRP_{\mathrm{MODIS},i}}
\right)
\]

The first quartile (\(Q_1\)), third quartile (\(Q_3\)), and interquartile range (IQR) are calculated across the matched sample population:

\[
IQR=Q_3-Q_1
\]

The accepted interval is:

\[
Q_1-1.5(IQR)
\leq q_i \leq
Q_3+1.5(IQR)
\]

Observations outside this interval are excluded from the calibration sample.

This screening is performed across the intended annual matched population rather than independently on arbitrary computational chunks.

#### Step 5. MODIS viewing zenith angle estimation

The MODIS viewing zenith angle (VZA) is estimated using the reported track dimension and a satellite observation geometry model.

The objective is to account for the effect of off-nadir viewing geometry on MODIS pixel dimensions and FRP retrievals.

Let:

- \(R_e\) denote the Earth radius;
- \(r_s\) denote the distance from the Earth's centre to the satellite;
- \(s\) denote the MODIS instantaneous field of view (IFOV);
- \(\Omega\) denote the satellite scan angle;
- \(S_{\mathrm{track}}\) denote the reported along-track pixel dimension.

The track dimension is modelled as:

\[
S_{\mathrm{track}} =
r_s s
\left[
\cos(\Omega)-
\sqrt{
\left(\frac{R_e}{r_s}\right)^2-
\sin^2(\Omega)
}
\right]
\]

The scan angle \(\Omega\) is estimated numerically by solving this equation for the observed track dimension.

The viewing zenith angle is then calculated as:

\[
VZA =
\arcsin\left(
\frac{r_s}{R_e}\sin(\Omega)
\right)
\]

The trigonometric calculations use radians internally, and the resulting VZA is converted into degrees for subsequent calibration.

The satellite-distance parameter \(r_s\) must represent the distance from the Earth's centre to the satellite, rather than the satellite altitude alone.

This is a geometry-based estimate derived from FIRMS footprint dimensions and the assumed sensor parameters. It should be validated against available MODIS viewing-angle information where possible.

#### Step 6. Empirical VZA-dependent MODIS FRP calibration

After anomalous samples have been removed, the remaining matched observations are used to estimate a viewing-angle-dependent correction factor for MODIS FRP.

For each matched observation:

\[
R_i =
\frac{FRP_{\mathrm{VIIRS,aggregated},i}}
{FRP_{\mathrm{MODIS},i}}
\]

The observations are grouped into 1-degree VZA bins.

For each bin \(k\), calculate the mean VZA and mean FRP ratio:

\[
\overline{\theta}_k =
\frac{1}{n_k}
\sum_{i\in k}\theta_i
\]

\[
R_k =
\frac{1}{n_k}
\sum_{i\in k}R_i
\]

where \(n_k\) is the number of matched observations in bin \(k\).

Bins containing fewer than five observations are excluded from polynomial fitting to reduce instability from sparsely populated viewing-angle ranges.

A second-degree polynomial is fitted to the bin-level mean ratios:

\[
R(\theta)=a\theta^2+b\theta+c
\]

where:

- \(\theta\) is the MODIS viewing zenith angle in degrees;
- \(a\), \(b\), and \(c\) are the fitted coefficients.

The polynomial is estimated using weighted least squares, with the square root of the number of observations in each bin used as the fitting weight:

$$
w_k=\sqrt{n_k}
$$

This gives greater influence to bins supported by more observations.

The resulting calibration function is used to estimate the MODIS FRP correction factor:

$$
FRP_{\mathrm{MODIS,adjusted},i}
=
R(\theta_i)\times FRP_{\mathrm{MODIS},i}
$$

Predictions are restricted to the fitted VZA range and positive correction factors. When the quadratic model cannot be fitted reliably, or a prediction is outside the valid fitted range, the overall median FRP ratio is used as a fallback correction factor.

This calibration aims to reduce systematic differences between MODIS and the spatially aggregated VIIRS reference, particularly those associated with viewing geometry.

#### Step 7. Quality-prioritized FRP fusion

After calibration, each matched MODIS footprint contains two FRP estimates:

1. Aggregated VIIRS FRP.
2. VZA-adjusted MODIS FRP.

The final FRP is selected using the standardized confidence ranks.

Let:

- \(C_{\mathrm{MODIS}}\) be the MODIS confidence rank;
- \(C_{\mathrm{VIIRS}}\) be the highest confidence rank among the VIIRS detections contributing to the MODIS footprint.

The fusion rule is:

$$
FRP_{\mathrm{harmonized},i}
=
\begin{cases}
FRP_{\mathrm{VIIRS,aggregated},i},
&
C_{\mathrm{VIIRS}}>C_{\mathrm{MODIS}}
\\
FRP_{\mathrm{MODIS,adjusted},i},
&
C_{\mathrm{VIIRS}}\leq C_{\mathrm{MODIS}}
\end{cases}
$$

Therefore:

- VIIRS supplies the final FRP when its contributing detections have a higher confidence rank than MODIS.
- MODIS supplies the final FRP when its confidence rank is higher or equal.
- Confidence ties are resolved in favour of MODIS.

The confidence rank used for the VIIRS aggregate is the maximum rank among its contributing detections. This represents the highest-confidence contributing VIIRS detection and is an explicit prioritization rule rather than a combined probabilistic confidence estimate.

Only MODIS footprints with at least one valid VIIRS spatial and temporal match are retained in the final output.

The output therefore maintains the MODIS footprint as its spatial reference while using the selected sensor's FRP estimate.

---

## 4. Final Harmonized Dataset

The final dataset is organized around the MODIS spatial footprint, with VIIRS observations aggregated to that reference footprint.

The main output fields are:

| Output feature | Description |
|---|---|
| latitude, longitude | MODIS footprint centre coordinates |
| scan, track | MODIS footprint dimensions |
| acq_date, acq_time, datetime_utc | MODIS acquisition date and time |
| satellite, instrument | Original MODIS platform and instrument identifiers |
| brightness, bright_t31 | Original MODIS brightness-temperature fields |
| bright_ti4, bright_ti5 | Mean VIIRS brightness temperatures from contributing detections |
| frp_modis_original | Original MODIS FRP after duplicate correction |
| frp_viirs_aggregated | Summed FRP of matched VIIRS detections |
| vza_deg | Estimated MODIS viewing zenith angle |
| calibration_ratio | Estimated VZA-dependent MODIS correction factor |
| frp_modis_adjusted | MODIS FRP after empirical calibration |
| frp_harmonized | Final FRP selected by the fusion procedure |
| fusion_source | Identifies whether the final FRP came from VIIRS or adjusted MODIS |
| confidence | Confidence value associated with the selected FRP source |
| confidence_class | Standardized confidence class of the selected source |
| confidence_selected_rank | Standardized confidence rank used during fusion |
| viirs_confidence_class | Confidence class of the highest-ranked contributing VIIRS detection |
| viirs_confidence_rank | Highest confidence rank among contributing VIIRS detections |
| viirs_match_count | Number of VIIRS detections aggregated into the MODIS footprint |
| viirs_match_time_delta_min | Minimum absolute temporal difference between the MODIS observation and contributing VIIRS detections |
| duplicate_count | Number of detections represented by the retained duplicate-group record |
| geometry_method | Footprint reconstruction method used |
| daynight, type, version | Original MODIS metadata and fire classification information |

The harmonized FRP field is the primary variable for subsequent fire activity analysis.

The original and intermediate FRP fields are retained to support quality assessment, reproducibility, and comparisons between the original sensor observations and the harmonized estimates.

---

## 5. Methodological Limitations and Considerations

Several limitations should be considered when interpreting the harmonized dataset.

1. **Approximate footprint geometry:** Pixel polygons are reconstructed from FIRMS centre coordinates and scan/track dimensions. They are not exact satellite geolocation polygons. The overlap and matching results therefore depend on the accuracy of this approximation.

2. **Sensor-specific spectral characteristics:** MODIS brightness, T31, VIIRS TI4, and VIIRS TI5 are retained separately. Their numerical values should not be interpreted as directly interchangeable measurements.

3. **Cloud correction is not applied:** The VIIRS FRP aggregate is not adjusted for cloud-covered area. Cloud-related omission and observation limitations may therefore remain in the reference FRP.

4. **Temporal mismatch:** A five-minute matching window reduces temporal differences but cannot eliminate actual changes in fire activity between observations.

5. **Confidence comparability:** The common confidence ranks provide an ordinal priority system, not a statistically calibrated equivalence between the two sensor confidence systems.

6. **Matched-only sampling:** The final dataset excludes MODIS footprints without a qualifying VIIRS match. This means the final dataset represents the subset of MODIS observations with near-synchronous VIIRS coverage, rather than the complete MODIS fire record.

7. **Empirical calibration:** The VZA-dependent correction is derived from the matched observations and depends on their spatial, temporal, and fire-intensity distributions. Its applicability should be evaluated across different regions, seasons, and viewing-angle ranges.

8. **Aggregation assumptions:** Summing VIIRS FRP within a MODIS footprint assumes that the contributing detections represent distinct fire contributions after duplicate correction. Spatial overlap, sub-pixel fire structure, and differing retrieval characteristics may still affect the aggregate.

9. **Platform differences:** Terra, Aqua, and NOAA-20 have different orbital and observation characteristics. The calibration and fusion results should be assessed for potential platform-specific effects.

---

## 6. References

1. Giglio, L., Schroeder, W., and Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*.  
   [MODIS Collection 6 and 6.1 Active Fire Product User's Guide](https://www.modis-fire.umd.edu/files/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf)

2. NASA Land Science Investigator Processing System. (2024). *VIIRS 375 m Active Fire Product User Guide*.  
   [VIIRS Collection 2 375 m Active Fire User Guide](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf)

3. Zheng, Y., Ding, K., Xue, L., Wang, Z., Jiao, G., Zhu, Y., Zhang, J., and Ren, Q. (2026). Fire Radiative Power Correction and Spatiotemporal Fusion Based on MYD14 and VNP14IMG. *Remote Sensing*, 18(10), 1650.  
   https://doi.org/10.3390/rs18101650

4. Schroeder, W., Oliva, P., Giglio, L., and Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96.  
   https://doi.org/10.1016/j.rse.2013.12.008

5. NASA. (2024). *Collection 2 VIIRS Burned Area Product User's Guide*, Version 1.1.  
   [VIIRS Collection 2 Burned Area User Guide](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_BA_User_Guide_1.1.pdf)

---

## 7. Methodological Basis

The overall framework is informed by recent research on MODIS–VIIRS FRP correction and spatiotemporal fusion, particularly the correction-before-fusion approach described by Zheng et al. (2026).

The present implementation adapts this general framework to the available data and project requirements. In particular, it combines Terra and Aqua MODIS observations with NOAA-20 VIIRS observations, uses an approximate FIRMS-based footprint reconstruction, omits area-based cloud correction, and applies the specified confidence-prioritized fusion strategy.

The resulting dataset is intended to provide a more internally consistent FRP record for long-term fire activity analysis while retaining the original sensor information needed for validation and further investigation.
