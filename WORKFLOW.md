# WORKFLOW — Hero Layout (Σύνθετος Χάρτης Κάλυψης Γης)
**Κατάσταση: v10 (λειτουργικό, εγκεκριμένο) — έτοιμο για νέα συνομιλία / επόμενες αλλαγές.**
Τελευταία ενημέρωση: 2026-06-07.

---

## 0. TL;DR — πώς συνεχίζω σε νέα συνομιλία
1. Διάβασε §6 (τρέχοντα knobs v10) και §8 (τι μένει να γίνει — ξεκίνα από εκεί).
2. Authoritative script: **`D:\thesis\Ch06_build\hero_layout\compose_hero.py`** (= v10). Το render (`render_hero_panels.py`) **δεν** ξανατρέχει εκτός αν αλλάξει το E.
3. Τρέξιμο:
```
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "D:\thesis\Ch06_build\hero_layout\compose_hero.py" 2>&1 | Select-Object -Last 6
```
4. Άνοιγμα αποτελέσματος για έλεγχο: `Filesystem:copy_file_user_to_claude` το `Hero_Layout.png` → `view`.

> ⚠️ **MCP**: οι local servers (Filesystem / Windows-MCP) κολλάνε διαλείποντα ~4 min σε μεγάλα `edit_file`/`write_file`. **Κλείσε** ανοιχτά αρχεία εξόδου (π.χ. το `Hero_Layout.png` σε viewer) **πριν** στείλεις μήνυμα ή τρέξεις — ανοιχτό handle «παγώνει» το chat. Fallback όταν πέφτει ο MCP: γράφω ολόκληρο το script στον χώρο του Claude (`/mnt/user-data/outputs/…`), το κατεβάζεις και το αντικαθιστάς, και το τρέχεις μόνος σου.

---

## 1. Concept
Ένας μεγάλος, καλλιτεχνικός σύνθετος χάρτης (poster) για το Κεφ.6 της διπλωματικής (7-Band vs RGB, DeepLabV3 + PointRend / ResNet-101, Πάμφιλα Μυτιλήνης).
Σύνθεση τριών διαγώνιων ζωνών με feathered μεταβάσεις:
- **nDSM** (πάνω-αριστερά): elevation ramp × hillshade.
- **Ταξινομημένη εικόνα** (μεσαία διαγώνιος, hero): shaded-relief σύνθεση (βλ. §6.2).
- **Θερμικό** (κάτω-δεξιά): inferno.
Συν: 4 κυκλικοί μεγεθυντικοί φακοί RGB με δείκτες, in-map ετικέτες κλάσεων, ιστογράμματα (nDSM/θερμικό), χάρακας, βορράς, inset Λέσβου, υπόμνημα/ράμπες/στοιχεία δεξιά, logos/QR.

---

## 2. Περιβάλλον & εκτέλεση
- **Python (ArcGIS Pro):** `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe` (arcpy, matplotlib, numpy, scipy, PIL). Status code 0 = επιτυχία.
- **Γράψιμο .py:** `Filesystem:write_file` / `Filesystem:edit_file` (UTF-8, Greek-safe). Σε μεγάλα edits κολλάει — τότε fallback (βλ. §0).
- **Έλεγχος εικόνας:** `Filesystem:copy_file_user_to_claude` το PNG → `view`.
- **Σημείωση filesystems:** `D:\…` = υπολογιστής χρήστη (Filesystem/Windows-MCP). `/mnt/…` = υπολογιστής Claude (create_file/view/bash).

---

## 3. File map
**Working dir:** `D:\thesis\Ch06_build\hero_layout\`
- `render_hero_panels.py` — STEP 1 (DONE). Knobs: `PAD_R=0, PAD_B=0` (E=nDSM extent), `CELL=0.12, RES=300, LENS_BUF=1.25`. Εξάγει: `_h_classified.png`, `_hero_arrays.npz` (ndsm/thermal/hillshade), `_lens_{Building,Vehicle,Road,Tree}.png`, `_hero_meta.json`.
- `compose_hero.py` — STEP 2 (= **v10**, authoritative).
- `compose_hero_v10.py` — αντίγραφο v10 (και στο `/mnt/user-data/outputs/` στον Claude).
- `WORKFLOW_hero_layout.md` — αυτό το αρχείο.
- Έξοδος: `Hero_Layout.png` / `Hero_Layout.pdf`.

**Source rasters (EPSG:32635):**
- RGB ortho (φακοί): `D:\thesis\prepare_trainig_data\prepare_training_data\results\composite_CS.tif`
- Ταξινομημένο: `…\results\deeplab_50a.tif` (τιμές 1–7)
- nDSM: `…\results\nDSM.tif`
- Θερμικό: `D:\thesis\pamgyla_thermal\Products\2D\True Ortho\pamgyla_thermal_True_Ortho.tif`
- Hillshade: `D:\thesis\pamfyla_pancro\Products\2D\DEM\DSMShadedRelief\pamfyla_pancro_dsm_shaded_relief.tif`
- mag_glass FC: `C:\Users\NickCoro\Desktop\post_proccesing\post_proccessing.gdb\mag_glass`
- aprx (μόνο ανάγνωση χρωμάτων): `D:\thesis\Ch06_build\tree_analysis_layout.aprx` (map «Map», layer `deeplab_50a.tif`)
- Assets: `D:\thesis\media\{uaegean-university.png, tmima_logo.png(384×123), RSGIS_logo.png(650×152), qr_github.png}`; `D:\thesis\Ch06_build\_inset.png` + `_inset_meta.json`.

---

## 4. Canonical values
- **E (extent):** `[458821.2, 4334032.4, 459318.4, 4334383.6]`, W≈497.2 m, H≈351.2 m, **asp≈1.416**, grid 4143×2927 @0.12 m.
- **Class % (full extent):** Bare Soil 48.5 · Tree 36.7 · Building 4.6 · Road 3.9 · Shadow-Noise 3.3 · Grass 2.9 · Vehicle 0.2.
- **Lens ground windows:** Building 29.65 m · Vehicle 14.51 m · Road 34.67 m · Tree 38.68 m.
- **Εύρη:** nDSM 0–25 m · θερμικό ≈19.3–61.9 °C.
- **Χρώματα κλάσεων στον χάρτη (v10, μετά recolor):** Tree `#1B5E20` · Grass `#8BC34A` · Building `#FF0000` · **Road `#000000`** · Vehicle `#FFFF00` · **Bare Soil `#895A44`** · **Shadow-Noise `#343434`**. Headings NAVY `#1F4E79`. (7-Band brand `#2E86AB`, RGB `#E63946` — δεν χρησιμοποιούνται εδώ.)
- **Διάταξη:** A4-agnostic «πλήρες custom layout» (λόγος ≈1.71). Κλίμακα γράφεται «≈ 1:1.100» (πλήρες μέγεθος καμβά).

---

## 5. STEP 1 — `render_hero_panels.py` (DONE)
Resample όλων στο E grid· εξαγωγή classified PNG, arrays (ndsm/thermal/hillshade με nan εκτός κάλυψης), 4 lens PNGs (square window, clipped σε κύκλο), `_hero_meta.json` (E, cell, asp, εύρη, lenses[cx,cy,ground_m,png,name_en]). **Ξανατρέχει μόνο αν αλλάξει το E.**

---

## 6. STEP 2 — `compose_hero.py` (v10) — τρέχοντα knobs

### 6.1 Καμβάς / χάρτης
- `FIGW=26.0, FIGH=15.2` in (λόγος ≈1.71). `MAP_X=0.020, MAP_W=0.700, MAP_TOP=0.905`· `MAP_H` από `ASP`· `MAP_Y=MAP_TOP−MAP_H`. `mf(fx,fy)` → figure coords.

### 6.2 Σύνθεση εικόνας χάρτη (ARTISTIC shaded-relief)
Σειρά (κάτω→πάνω): **ταξινομημένη `alpha=0.70`** (z1) → **hillshade grayscale RGBA `alpha=0.50`** (z1.2, alpha=0 όπου nan) → **rgba_nd** ζώνη nDSM (z2) → **rgba_th** ζώνη θερμικού (z3). Recolor ταξινομημένης (ΣΕΙΡΑ έχει σημασία): Road `#343434`→`#000000` **πριν** Shadow `#828282`→`#343434`, μετά Bare Soil `#C3A46F`→`#895A44`. (Tree `#737300`→`#1B5E20`, Grass `#D3FFBE`→`#8BC34A`.)
> ⚠️ Το global hillshade «μπαίνει» ελαφρά και στις ζώνες nDSM/θερμικού στα feather edges. Αν φανεί βαρύ → mask hillshade μόνο στη μεσαία (classified) ζώνη.

### 6.3 In-map ετικέτες κλάσεων
1 ανά κλάση στο πιο «εσωτερικό» σημείο (distance_transform_edt σε color-mask) + extra «Κτίρια» στο πυκνό κάτω-αριστερά σύμπλεγμα.
- **AREA classes {Grass,Bare Soil,Shadow}** = χαρτογραφικό ύφος περιοχής: πλάγια, **letter-spaced** (thin-space `\u2009` ανά γράμμα), uppercase χωρίς τόνους (`gup()`), αποχρωματισμένη απόχρωση `AREA_DARK={6:#5E3D2E,5:#2E5A1E,7:#1F1F1F}`, λευκό halo, fontsize 13. **(ΕΥΘΕΙΑ γραμμή προς το παρόν — βλ. §8.4 για curved.)**
- **Point classes {Tree,Building,Road,Vehicle}** = έντονα λευκά + σκούρο halo.
- `CLS_HEX` (για masks) ενημερωμένο: 3→`#000000`, 7→`#343434`, 6→`#895A44`.

### 6.4 Φακοί (κυκλικά footprints)
Map-fraction `LENS_FRAC`: Vehicle(0.45,0.82) · Road(0.80,0.80) · Tree(0.88,0.29) · **Building=(0.26, εφαπτόμενος κάτω: `fy=(LENS_R*FIGW/FIGH)/MAP_H`)**. `LENS_R=0.046`.
- Footprint = **ΚΥΚΛΟΣ** radius `ground_m/2` πάνω στον χάρτη (λευκό+navy)· δείκτης από φακό στην **ακμή** του κύκλου.
- Μέσα στον φακό: «1:n» πάνω· όνομα κλάσης σε **καμπύλο «χαμόγελο»** κάτω (span=len×10.5°, r=0.40, rotation=θ−270).

### 6.5 Ιστογράμματα
nDSM (πάνω, glued `fy_b=0.915`) & θερμικό (κάτω, `fy_b=0.020`), μικρά, soft white wash alpha 0.20, halo αριθμοί, **κεντραρισμένα σε κελί καννάβου** (`g0+50`, `g0+350`).

### 6.6 Χάρακας / βορράς
Χάρακας 100 m (5×20), κεντραρισμένος κάτω, ημιδιάφανος (alpha 0.80), `sy=Y0+sh*0.085`. Βορράς «Β» πάνω-δεξιά.

### 6.7 Δεξιά στήλη (flowing cursor `cy`, `LX=0.738, RR=0.985`)
inset Λέσβου (στρογγυλό, αστέρι, km-scale, βορράς) → γραμμή → **υπόμνημα**: ξεχωριστά πλακίδια `sww=0.020×swh=0.012` με κενά (`dyr=0.021`) + ξεχωριστές μπάρες % (`LBAR0=0.882, LBARW=0.072, barh=0.013`) → γραμμή → μεγεθυντικός φακός (σύμβολο+περιγραφή) → γραμμή → ράμπες nDSM(0–25) & θερμοκρασία(20–60) → γραμμή → **Στοιχεία χάρτη**.
- Διαχωριστικές γραμμές `hline()` `#cfcfcf` σε όλα τα section breaks.

### 6.8 Στοιχεία χάρτη
Περιοχή/Αισθητήρας/Μοντέλο/GSD 4,52 cm/EPSG:32635/Κάνναβος 100 m / **Έκταση ≈500×350 m** / **Γωνίες: ΒΔ 458.820, 4.334.380 · ΝΑ 459.320, 4.334.030** (δεκάδα, `gr10`) / **Κλίμακα ≈ 1:1.100** / Πηγή / Επιβλέπων Δρ. Χρ. Βασιλάκος · Δημιουργός Ν. Κορωνιάδης / Ιούνιος 2026. (Η σημείωση nDSM-extent ΑΦΑΙΡΕΘΗΚΕ.)

### 6.9 Logos / τίτλος
uaegean (πάνω-αρ.) + QR με πλαίσιο (κάτω-αρ.) ίσα τετράγωνα· tmima (πάνω-δεξ.) + RSGIS (κάτω-δεξ.) ίσο ύψος. Τίτλος κεντραρισμένος πάνω από τον χάρτη, 24 pt NAVY.

---

## 7. Ιστορικό feedback (v1→v10) — όλα ΟΛΟΚΛΗΡΩΜΕΝΑ
- **v1–v2:** concept· recolor Tree/Grass· E=nDSM· ράμπες υπομνήματος· inset fix· ιστογράμματα μικρά/διάφανα/halo· info δεξιά.
- **v3:** φακοί μέσα στον χάρτη· χωρίς υπότιτλο τίτλου· y-labels έξω· inset στρογγυλό+κλίμακα+βορράς.
- **v4:** χάρτης ψηλά (ευθυγρ. με inset)· υπόμνημα πλακίδια· αφαίρεση λευκών zone-labels· QR πλαίσιο.
- **v5:** βορράς πάνω-δεξιά· in-map class labels· crop κάτω κενού (FIGH→15.2)· χάρακας 100 m κεντρ.
- **v6:** καμπύλες ετικέτες φακών· «Κτίρια» κάτω-αρ.· διαχωρισμός φακού/ραμπών· φακός σπιτιού στο κάτω όριο.
- **v7:** πυκνότερα γράμματα φακών· χάρακας ημιδιάφανος/ψηλότερα· **MAP_W 0.66→0.70**· ξεχωριστές μπάρες %· διαχωριστικές γραμμές· ιστογράμματα σε κελί· έκταση=διαστάσεις.
- **v8:** ιστόγραμμα nDSM glued top· **πλήρες custom (κλίμακα 1:1.100)**· δεκάδα· **ξεχωριστά πλακίδια υπομνήματος**· γωνιακές συντεταγμένες (αρχικά on-map)· αφαίρεση nDSM note.
- **v9:** γωνίες **μεταφέρθηκαν στα Στοιχεία** (off-map)· καθαρή κλίμακα· **χαρτογραφικά area-labels** (italic+letter-spaced)· footprint **τετράγωνο** + δείκτης σε γωνία.
- **v10:** footprint **ΚΥΚΛΟΣ** + δείκτης σε ακμή· **shaded-relief σύνθεση** (classified 30% + hillshade 50%)· **Road→μαύρο, Shadow→#343434, Bare Soil→#895A44**.

---

## 8. ΕΚΚΡΕΜΗ — επόμενες αλλαγές (ΞΕΚΙΝΑ ΑΠΟ ΕΔΩ)
> Σειρά εργασίας: εφάρμοσε 1–4 → render → μετά 5 (sampling από τελικό render).

**8.1 — Δρόμος πιο μαύρος.** Τώρα Road=`#000000` αλλά το hillshade(50%)+classified(70%) τον γκριζάρει. Λύση: σχεδίασε τα road pixels ως **opaque μαύρη μάσκα ΠΑΝΩ από το hillshade** (π.χ. ξεχωριστό overlay `mask(CLS_HEX[3])` με alpha~0.9, zorder 1.3), ή αύξησε τοπικά την αδιαφάνεια της ταξινόμησης στον δρόμο. Στόχος: σαφής διάκριση από Shadow `#343434`.

**8.2 — Γρασίδι λιγότερο φωτεινό.** Σκούρυνε `GRASS_NEW` `#8BC34A`→δοκίμασε `#7CB342` ή `#689F38` (ή μείωσε lightness). Ενημέρωσε και `ratcol["Grass"]` + recolor source.

**8.3 — Γυμνό έδαφος πιο καφέ.** Το `#895A44` βγαίνει ροζ-μπεζ λόγω wash. Δοκίμασε πιο κορεσμένο/σκούρο: `#7A4A36` ή `#6E4631`. Ενημέρωσε recolor + `ratcol["Bare Soil"]` + `CLS_HEX[6]` + `AREA_DARK[6]`.

**8.4 — CURVED area-labels (Γρασίδι, Γυμνό έδαφος, Σκίαση).** Σαν ετικέτες ωκεανού σε άτλαντα: τα γράμματα να ακολουθούν **ήπια καμπύλη** (bezier/τόξο) πάνω στο feature, αντί ευθεία. Υλοποίηση: για κάθε area-class υπολόγισε άξονα/προσανατολισμό της μάζας (π.χ. PCA της μάσκας ή κεντρική γραμμή), τοποθέτησε χαρακτήρες κατά μήκος καμπύλης με per-char rotation (όπως οι φακοί). Κράτα italic+letter-spacing+halo. **Μεγαλύτερη αλλαγή — δικό της section.**

**8.5 — Update χρωμάτων υπομνήματος ώστε να ΤΑΙΡΙΑΖΟΥΝ με τον χάρτη.** Επειδή ο χάρτης είναι washed (classified 70% + hillshade 50%), τα pure swatches δεν αποτυπώνουν την εμφάνιση. Μετά τα 8.1–8.4: **δειγμάτισε από το τελικό render** την αντιπροσωπευτική (median) απόχρωση κάθε κλάσης μέσα στη μεσαία ζώνη και βάλ' την στα swatches (ή, απλούστερα, swatch = pure×0.70 over white). Στόχος: υπόμνημα ↔ χάρτης συνέπεια.

---

## 9. Open / optional
- Mask hillshade μόνο στη μεσαία ζώνη αν φανεί βαρύ στις ζώνες nDSM/θερμικού (§6.2).
- Πιθανό «μούντωμα» ζώνης nDSM πάνω-αριστερά.


---

## 10. v11 → v12 (cowork iteration, 2026-06-07)

> Iterated in `cowork_workspace\` with an **arcpy-free engine** (`compose_hero_param.py`) that renders from the cached artefacts (`_hero_arrays.npz`, `_hero_meta.json`, `_h_classified.png`, `_lens_*.png`) so combinations can be swept fast outside ArcGIS Pro. Each run is id-tagged and logged to `runs_log.csv/.txt`. The chosen knobs are baked into stand-alone arcpy scripts. **Outputs are non-destructive** (`Hero_Layout_v11.*`, `Hero_Layout_v12a.*`, `Hero_Layout_v12b.*`) and each writes `compose_runs_log.txt` with id == image suffix.

### v11 — `cowork_workspace\compose_hero_v11.py` (= compose_hero.py + only these lines)
- **Γρασίδι** less bright: `GRASS_NEW #8BC34A→#689F38→#5E8C3A→#588233` (final #588233 in v12).
- **nDSM top-left** less black: floor `0.45→0.66` (`elev_rgb*(ND_FLOOR+(1-ND_FLOOR)*shade)`).
- **Θερμικό** got hillshade relief: `TH_HS_DARK=0.45, TH_HS_LITE=0.25` (bidirectional multiply on inferno).
- **Σκεπές** keep hillshade: dedicated Building relief boost `ROOF_DARK=0.55, ROOF_LITE=0.12`.
- **Κόκκινο** κτιρίων less/more intense: `RED_NEW #FF0000→#E5392E→#EE2E22` (final #EE2E22).
- **Classified opacity**: `0.82→0.77→0.81→0.79` (final 0.79; lower = more hillshade through).
- **Σκίαση label** moved onto the tree cast-shadow (see v12 for final offset).
- Output dpi raised to **300**.

### v12a — `cowork_workspace\compose_hero_v12a.py` (= v11 + )
- **Σκίαση label**: final offset `dx=-0.0109, dy=-0.00276` (fractions of map W/H) + **font 8→7**. (Print-scale nudges: map prints ≈46.2×32.65 cm; total ≈ down + into the grey shadow, slightly right.)
- **PDF glyph fix**: `plt.rcParams["pdf.fonttype"]=42; ps.fonttype=42` → embed TrueType so Greek glyphs (e.g. «ι») render correctly in the PDF (was Type-3).
- **Classified opacity** 0.79 (+2% transparency vs 0.81).

### v12b — `cowork_workspace\compose_hero_v12b.py` (= v12a + )
- **nDSM ramp low end → neutral slate-grey** (so low elevation no longer looks like Tree/Grass green):
  `ELEV = ["#3B4248","#8C9094","#C3B488","#E8DFC2","#F7F1DE"]` (high end keeps the warm tan/cream).

### Final knobs (v12b)
`GRASS=#588233 · BARE=#7A4A36 · TREE=#1B5E20 · BUILDING/RED=#EE2E22 · ROAD=#000000 · SHADOW=#343434 · VEHICLE=#FFFF00`
`CLASSIFIED_ALPHA=0.79 · RELIEF_DARK=0.62 · RELIEF_LITE=0.34 · ROAD_ALPHA=0.25 · ND_FLOOR=0.66`
`TH_HS_DARK=0.45 · TH_HS_LITE=0.25 · TH_ZONE_ALPHA=0.94 · ROOF_DARK=0.55 · ROOF_LITE=0.12`
`Σκίαση label dx=-0.0109 dy=-0.00276 fs=7 · ELEV ramp = slate→tan · dpi=300 · pdf/ps.fonttype=42`

### Run (ArcGIS Pro python)
```
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "D:\thesis\Ch06_build\hero_layout\cowork_workspace\compose_hero_v12b.py"
```

### Status / next
- **Authoritative working script remains `compose_hero.py` (v10).** v12b is the approved look but lives in `cowork_workspace\`. To promote: copy `cowork_workspace\compose_hero_v12b.py` → `compose_hero.py` (and let it overwrite `Hero_Layout.png/.pdf`).
- Informative HTML of the whole process: `cowork_workspace\hero_layout_story.html`.
