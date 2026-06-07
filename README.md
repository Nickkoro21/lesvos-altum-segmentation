# 🗺️ Land-Cover Composite Map — Pamfila, Lesvos

**Cartographic composite of a UAV land-cover classification**, integrating elevation (nDSM),
the 7-class semantic-segmentation result, and a thermal channel into a single shaded-relief
poster, with an interactive web companion that documents the cartographic workflow.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Live · GitHub Pages](https://img.shields.io/badge/Live-GitHub%20Pages-2C6CA8?logo=github&logoColor=white)](https://nickkoro21.github.io/lesvos-altum-segmentation/)
[![Built with Python](https://img.shields.io/badge/Built%20with-Python%20%2B%20Matplotlib-3776AB?logo=python&logoColor=white)](https://matplotlib.org/)
[![ArcGIS Pro](https://img.shields.io/badge/ArcGIS%20Pro-3.6-2C7AC3?logo=arcgis&logoColor=white)](https://www.esri.com/)
[![MSc Thesis](https://img.shields.io/badge/MSc%20Thesis-University%20of%20the%20Aegean-1F4E79)](https://geography.aegean.gr/)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nick%20Koroniadis-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nick-koroniadis-328962226/)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-NickKoro21-FFD21E)](https://huggingface.co/NickKoro21)
[![GitHub](https://img.shields.io/badge/GitHub-Nickkoro21-181717?logo=github&logoColor=white)](https://github.com/Nickkoro21)

[🌐 **Live page**](https://nickkoro21.github.io/lesvos-altum-segmentation/) · [🗺️ **Map design**](#map-design) · [🛰️ **Data--method**](#data--method) · [👤 **Author**](#author--affiliations) · [📚 **Citation**](#citation)

---

## Overview

This repository hosts an **interactive web page** (GitHub Pages) that explains how a cartographic
land-cover composite was produced over **Pamfila, Lesvos (Greece)**, together with the **Python
rendering pipeline** that generates the final poster. The work is part of an MSc thesis at the
**University of the Aegean** (Department of Geography, RSGIS Lab), supervised by **Dr. Christos Vasilakos**.

Source imagery comes from a **MicaSense Altum-PT** sensor. A **DeepLabV3+ PointRend (ResNet-101)**
model classifies the scene into **7 land-cover classes** — Tree, Building, Road, Vehicle, Grass,
Bare Soil, Shadow-Noise — and the map integrates that classification with **nDSM** (height) and a
**thermal** channel.

> **Language note:** the web page is written in **Greek**, with standard English terminology kept
> (DeepLabV3+, PointRend, ResNet-101, nDSM, hillshade).

## 🌐 Live page

**<https://nickkoro21.github.io/lesvos-altum-segmentation/>**

The page (`docs/`) includes:

| Section | Content |
| --- | --- |
| **Overview** | Final poster with full-screen view, zoom and **PNG / PDF download**. |
| **Input data** | Sensor, classes and per-class coverage. |
| **3+1 Views** | nDSM, classification, thermal + RGB with **synchronized zoom / pan** (shared extent). |
| **Diagonal composition** | Adjustable per-zone footprint (nDSM top-left, thermal bottom-right, classification remainder; sum = 100%). |
| **Tools · Ratios & colours · Path v1→v12** | Implementation stack, layout geometry, palette, design history. |

Every image supports full-screen, zoom in/out, keyboard-arrow panning, reset and exit.

## Map design

- **Composite of three diagonal zones** with feathered transitions: nDSM (top-left), classification
  (centre), thermal (bottom-right).
- **Shaded-relief synthesis**: each layer is modulated by a hillshade (bidirectional multiply) to
  retain both colour and texture.
- **nDSM ramp**: neutral slate → tan (low elevation intentionally non-vegetation-green).
- **Thermal**: `inferno` colour map (~20-60 °C) with a light hillshade overlay.
- **Output**: A-ratio-agnostic custom layout (≈ 1.71), rendered at **300 dpi** (7800 × 4560 px).

## 🛰️ Data & method

- **Sensor:** MicaSense Altum-PT (multispectral + thermal + panchromatic).
- **Model:** DeepLabV3+ PointRend, ResNet-101 backbone, 7-Band input, 7 land-cover classes.
- **Reference system:** EPSG:32635 (UTM 35N) · GSD 4.52 cm · area ≈ 500 × 350 m.

## Repository structure

```
lesvos-altum-segmentation/
├── docs/                      ← GitHub Pages site
│   ├── index.html             ← interactive page
│   ├── assets_html/           ← co-registered layer images (nDSM, classified, thermal, RGB)
│   └── downloads/             ← hero_map.png (300 dpi) + hero_map.pdf
├── src/
│   ├── render_hero_panels.py  ← STEP 1: resample sources to a common extent, export panels
│   └── compose_hero.py        ← STEP 2: compose the final poster (matplotlib)
├── WORKFLOW.md                ← full design notes / change history
├── README.md
└── LICENSE
```

## Reproducing the poster

The scripts require **ArcGIS Pro** Python (`arcgispro-py3`, with `arcpy`) and the original raster
sources (not published). They contain local absolute paths and are provided as a methodological
reference rather than a stand-alone executable.

```bash
# STEP 1 (only if the canvas extent changes)
"%ProgramFiles%\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" src\render_hero_panels.py
# STEP 2 — render the final poster (Hero_Layout.png / .pdf, 300 dpi)
"%ProgramFiles%\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" src\compose_hero.py
```

## 👤 Author & affiliations

**Nikolaos Koroniadis** — MSc Geography and Applied Geoinformatics, Department of Geography,
[University of the Aegean](https://www.aegean.gr/), Remote Sensing & GIS Research Group (RSGIS Lab).

**Thesis supervisor:** Dr. Christos Vasilakos.

## 🔗 Related projects

- 📊 [**7-Band vs RGB — Results Dashboard**](https://github.com/Nickkoro21/thesis-7band-vs-rgb) ([live](https://nickkoro21.github.io/thesis-7band-vs-rgb/))
- 🧰 [**PostProcessing Toolbox**](https://github.com/Nickkoro21/PostProcessing-Toolbox)
- 🎲 [**JM Separability Toolbox**](https://github.com/Nickkoro21/jm-separability-toolbox)

## 📚 Citation

```bibtex
@software{koroniadis2026landcovermap,
  author    = {Koroniadis, Nikolaos},
  title     = {{Land-Cover Composite Map of Pamfila, Lesvos: Cartographic
               Synthesis of UAV Multispectral, nDSM and Thermal Data}},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/Nickkoro21/lesvos-altum-segmentation},
  note      = {MSc Thesis deliverable, University of the Aegean, RSGIS Lab}
}
```

## 🙏 Acknowledgments

- **Dr. Christos Vasilakos** — thesis supervision.
- **University of the Aegean, RSGIS Lab** — academic environment and resources.
- **Anthropic Claude** — AI-assisted development of the rendering pipeline and web page.
- **GitHub** — free hosting via GitHub Pages.

## 📄 License

Released under the [MIT License](LICENSE).

---

RSGIS Lab · Department of Geography · University of the Aegean · Mytilene, Greece · 2026
