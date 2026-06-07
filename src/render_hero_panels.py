# -*- coding: utf-8 -*-
"""
render_hero_panels.py  --  STEP 1 of the hero layout pipeline.
Renders aligned source panels over a common canvas extent E (= nDSM extent
padded right/bottom), to be composed in matplotlib by compose_hero.py.
Outputs (in hero_layout\):
  _h_classified.png      RGB, full E (base = hero)
  _hero_arrays.npz       ndsm / thermal / hillshade arrays on the E grid (NR x NC)
  _lens_<name>.png       RGB ortho crop per mag_glass feature (4)
  _hero_meta.json        E, grid, value ranges, lens info
No aprx save. Run with arcgispro-py3 python via Windows-MCP:PowerShell.
"""
import arcpy, os, json
import numpy as np

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

WORK = r"D:\thesis\Ch06_build\tree_analysis_layout.aprx"
OUT  = r"D:\thesis\Ch06_build\hero_layout"
MAG  = r"C:\Users\NickCoro\Desktop\post_proccesing\post_proccessing.gdb\mag_glass"
SR   = arcpy.SpatialReference(32635)
RAST = {
 "ortho":      r"D:\thesis\prepare_trainig_data\prepare_training_data\results\composite_CS.tif",
 "classified": r"D:\thesis\prepare_trainig_data\prepare_training_data\results\deeplab_50a.tif",
 "ndsm":       r"D:\thesis\prepare_trainig_data\prepare_training_data\results\nDSM.tif",
 "thermal":    r"D:\thesis\pamgyla_thermal\Products\2D\True Ortho\pamgyla_thermal_True_Ortho.tif",
 "hillshade":  r"D:\thesis\pamfyla_pancro\Products\2D\DEM\DSMShadedRelief\pamfyla_pancro_dsm_shaded_relief.tif",
}
CLS_NAME = {1:("Tree","Δέντρο"),2:("Building","Κτίριο"),3:("Road","Δρόμος"),
            4:("Vehicle","Όχημα"),5:("Grass","Γρασίδι"),6:("Bare Soil","Γυμνό έδαφος"),
            7:("Shadow-Noise","Σκίαση/θόρυβος")}

# ----- KNOBS -----
PAD_R = 0.0    # m: only the nDSM footprint (no right extension)
PAD_B = 0.0    # m: ... and no bottom extension
CELL  = 0.12    # m: display cell for continuous arrays (start coarse; refine later)
RES   = 300     # dpi for ArcGIS exports
PW_MM = 420.0   # classified panel page width (aspect from E)
LENS_BUF = 1.25 # square buffer factor around each lens window
LENS_MM  = 120.0

aprx = arcpy.mp.ArcGISProject(WORK)

# ---- canvas extent E (= nDSM, padded R/B, capped to ortho) ----
nd = arcpy.Raster(RAST["ndsm"]).extent
orth = arcpy.Raster(RAST["ortho"]).extent
therm = arcpy.Raster(RAST["thermal"]).extent
xmin = nd.XMin
ymax = nd.YMax
xmax = min(nd.XMax + PAD_R, orth.XMax, therm.XMax)
ymin = max(nd.YMin - PAD_B, orth.YMin, therm.YMin)
E = arcpy.Extent(xmin, ymin, xmax, ymax)
W = xmax - xmin; H = ymax - ymin; ASP = W / H
NC = int(round(W / CELL)); NR = int(round(H / CELL))
print("E = [%.1f %.1f %.1f %.1f]  W=%.1f H=%.1f asp=%.3f  grid=%dx%d @%.2fm" %
      (xmin, ymin, xmax, ymax, W, H, ASP, NC, NR, CELL))

def export_map(mapname, vis_name, png, ext, pw_mm):
    m = aprx.listMaps(mapname)[0]
    for ly in m.listLayers():
        try: ly.visible = (ly.name == vis_name)
        except Exception: pass
    ph_mm = pw_mm / ((ext.XMax-ext.XMin)/(ext.YMax-ext.YMin))
    L = aprx.createLayout(pw_mm, ph_mm, "MILLIMETER", "_L_"+os.path.basename(png))
    arr = arcpy.Array([arcpy.Point(0,0),arcpy.Point(pw_mm,0),arcpy.Point(pw_mm,ph_mm),
                       arcpy.Point(0,ph_mm),arcpy.Point(0,0)])
    fr = L.createMapFrame(arcpy.Polygon(arr), m, "f")
    fr.camera.setExtent(ext)
    L.exportToPNG(png, resolution=RES)
    print("  exported", os.path.basename(png))

# ---- classified base (RGB) over E ----
export_map("Map", "deeplab_50a.tif", os.path.join(OUT,"_h_classified.png"), E, PW_MM)

# ---- continuous arrays on the E grid (resample -> read, nodata=nan) ----
arcpy.env.outputCoordinateSystem = SR
arcpy.env.snapRaster = RAST["classified"]
arcpy.env.extent = E
def to_grid(key, method):
    out = os.path.join(OUT, "_g_%s.tif" % key)
    arcpy.management.Resample(RAST[key], out, str(CELL), method)
    return out
nd_g = to_grid("ndsm", "BILINEAR")
th_g = to_grid("thermal", "BILINEAR")
hs_g = to_grid("hillshade", "BILINEAR")
arcpy.env.extent = None
def read_to_E(path, band_mean=False):
    r = arcpy.Raster(path); re = r.extent
    try:
        a = arcpy.RasterToNumPyArray(r, nodata_to_value=np.nan).astype("float32")
    except ValueError:
        a = arcpy.RasterToNumPyArray(r).astype("float32")
    if a.ndim == 3:
        a = a.mean(axis=0) if band_mean else a[0]
    col0 = int(round((re.XMin - E.XMin)/CELL))
    row0 = int(round((E.YMax - re.YMax)/CELL))
    full = np.full((NR, NC), np.nan, dtype="float32")
    h0, w0 = a.shape
    r0, c0 = max(row0,0), max(col0,0)
    ar, ac = r0-row0, c0-col0
    hh = min(h0-ar, NR-r0); ww = min(w0-ac, NC-c0)
    if hh>0 and ww>0:
        full[r0:r0+hh, c0:c0+ww] = a[ar:ar+hh, ac:ac+ww]
    return full
ndsm = read_to_E(nd_g)
ther = read_to_E(th_g)
hs   = read_to_E(hs_g, band_mean=True)
r, c = NR, NC
print("  arrays E-grid:", ndsm.shape,
      " ndsm nanfrac=%.2f thermal nanfrac=%.2f" % (np.isnan(ndsm).mean(), np.isnan(ther).mean()))
np.savez_compressed(os.path.join(OUT,"_hero_arrays.npz"), ndsm=ndsm, thermal=ther, hillshade=hs)

# ---- lens ortho crops (4) ----
lenses = []
with arcpy.da.SearchCursor(MAG, ["OID@","class","SHAPE@"]) as cur:
    feats = [(o,int(cl),s) for o,cl,s in cur]
for oid, cl, shp in feats:
    e = shp.extent; cx=(e.XMin+e.XMax)/2.0; cy=(e.YMin+e.YMax)/2.0
    side = max(e.XMax-e.XMin, e.YMax-e.YMin) * LENS_BUF
    le = arcpy.Extent(cx-side/2, cy-side/2, cx+side/2, cy+side/2)
    en, el = CLS_NAME[cl]
    png = os.path.join(OUT, "_lens_%s.png" % en.replace(" ","_"))
    export_map("M_ortho", "composite_CS.tif", png, le, LENS_MM)
    lenses.append({"oid":oid,"class":cl,"name_en":en,"name_el":el,
                   "cx":cx,"cy":cy,"ground_m":round(side,2),
                   "ext":[le.XMin,le.YMin,le.XMax,le.YMax],"png":os.path.basename(png)})

meta = {
 "E":[xmin,ymin,xmax,ymax], "W":W, "H":H, "asp":ASP, "cell":CELL, "NC":c, "NR":r,
 "ndsm_range":[0.0, 25.0988], "thermal_range":[19.3277, 61.8514],
 "classified_png":"_h_classified.png", "arrays_npz":"_hero_arrays.npz",
 "lenses":lenses,
}
json.dump(meta, open(os.path.join(OUT,"_hero_meta.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("META lenses:", [(l["name_en"], l["ground_m"]) for l in lenses])
print("DONE")
