# -*- coding: utf-8 -*-
"""compose_hero.py -- STEP 2 (PROMOTED from v12b). Authoritative. Outputs Hero_Layout.png/.pdf.
grass #689F38, ND_FLOOR=0.66, thermal hillshade 0.45/0.25, roof boost 0.55/0.12,
Skiasi label up-left. Outputs Hero_Layout_v11.png/.pdf (non-destructive)."""
import arcpy, os, json, math, colorsys, textwrap, unicodedata
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.image as mpimg
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.path import Path as MPath
from scipy.ndimage import gaussian_filter, zoom, distance_transform_edt

OUT  = r"D:\thesis\Ch06_build\hero_layout"
WORK = r"D:\thesis\Ch06_build\tree_analysis_layout.aprx"
MEDIA= r"D:\thesis\media"
EMB  = os.path.join(MEDIA,"uaegean-university.png"); DLOGO=os.path.join(MEDIA,"tmima_logo.png")
RSGIS= os.path.join(MEDIA,"RSGIS_logo.png"); QR=os.path.join(OUT,"qr_app.png")   # (v12b+) QR -> live web app
INSET= r"D:\thesis\Ch06_build\_inset.png"; INSET_META=r"D:\thesis\Ch06_build\_inset_meta.json"
CLASSIFIED_FULL = r"D:\thesis\prepare_trainig_data\prepare_training_data\results\deeplab_50a.tif"
THERMAL_FULL    = r"D:\thesis\pamgyla_thermal\Products\2D\True Ortho\pamgyla_thermal_True_Ortho.tif"

NAVY="#1F4E79"; GREY="#444444"; TREE_NEW="#1B5E20"; GRASS_NEW="#588233"; BARE_NEW="#7A4A36"; RED_NEW="#EE2E22"
CLS_NAME={1:"Δέντρο",2:"Κτίριο",3:"Δρόμος",4:"Όχημα",5:"Γρασίδι",6:"Γυμνό έδαφος",7:"Σκίαση/θόρυβος"}
CLS_EN  ={1:"Tree",2:"Building",3:"Road",4:"Vehicle",5:"Grass",6:"Bare Soil",7:"Shadow-Noise"}
CLS_HEX ={1:TREE_NEW,2:RED_NEW,3:"#000000",4:"#FFFF00",5:GRASS_NEW,6:BARE_NEW,7:"#343434"}
MAP_LABEL={6:"Γυμνό έδαφος",1:"Δέντρο",2:"Κτίριο",3:"Δρόμος",5:"Γρασίδι",7:"Σκίαση",4:"Όχημα"}
LENS_EL ={"Vehicle":"ΟΧΗΜΑ","Road":"ΔΡΟΜΟΣ","Building":"ΚΤΙΡΙΟ","Tree":"ΔΕΝΤΡΟ"}

FIGW, FIGH = 26.0, 15.2; R=FIGH/FIGW
MAP_X, MAP_W, MAP_TOP = 0.020, 0.700, 0.905
FEATHER_M = 16.0; ND_AX, ND_BY = 0.58, 0.60; TH_BX, TH_CY = 0.40, 0.42; GRID_STEP = 100.0
CLASSIFIED_ALPHA = 0.79; RELIEF_DARK = 0.62; RELIEF_LITE = 0.34; ROAD_ALPHA = 0.25   # (v12) classified opacity 0.79 (= +2% transparency vs 0.81); shows more hillshade
ND_FLOOR = 0.66                       # (v11) nDSM zone darkness floor (higher => less black top-left)
TH_HS_DARK = 0.45; TH_HS_LITE = 0.25  # (v11) hillshade relief on the thermal zone (0,0 => off)
ROOF_DARK = 0.55; ROOF_LITE = 0.12    # (v11) stronger relief on Building roofs (0,0 => use global RELIEF_*)
TH_ZONE_ALPHA = 0.94                  # (v11) thermal layer opacity (<1 => -6% lets underlying info through)
LABEL_MAX_TILT = 22.0; LABEL_STEP_FRAC = 0.019                 # (8.4) curved area-label knobs
LENS_FRAC = {"Vehicle":(0.45,0.82), "Road":(0.80,0.80), "Tree":(0.88,0.29), "Building":(0.26,0.099)}
LENS_R = 0.046

meta=json.load(open(os.path.join(OUT,"_hero_meta.json"),encoding="utf-8"))
E=meta["E"]; X0,Y0,X1,Y1=E; CELL=meta["cell"]; ASP=meta["asp"]
z=np.load(os.path.join(OUT,"_hero_arrays.npz")); ndsm=z["ndsm"]; ther=z["thermal"]; hs=z["hillshade"]
NR,NC=ndsm.shape
classified=mpimg.imread(os.path.join(OUT, meta["classified_png"])).copy()
ND_RANGE=meta["ndsm_range"]; TH_RANGE=meta["thermal_range"]

def hx(h): h=h.lstrip("#"); return np.array([int(h[i:i+2],16) for i in (0,2,4)])/255.0
def recolor(img, old_hex, new_hex, tol=0.06):
    o=hx(old_hex); n=hx(new_hex); m=np.abs(img[...,:3]-o).sum(2)<tol
    for k in range(3): img[...,k][m]=n[k]
    return img
classified=recolor(classified,"#737300",TREE_NEW); classified=recolor(classified,"#D3FFBE",GRASS_NEW)
classified=recolor(classified,"#343434","#000000")   # (2) Road -> pure black (BEFORE shadow recolor)
classified=recolor(classified,"#828282","#343434")   # (2) Shadow-Noise -> dark grey
classified=recolor(classified,"#C3A46F",BARE_NEW)    # (2/8.3) Bare Soil -> warm brown
if RED_NEW!="#FF0000": classified=recolor(classified,"#FF0000",RED_NEW)   # (v11) Building red less bright/intense

def cim_hex(co):
    t=type(co).__name__; v=list(co.values)
    if "HSV" in t: r,g,b=[c*255 for c in colorsys.hsv_to_rgb(v[0]/360.,v[1]/100.,v[2]/100.)]
    elif "HSL" in t: r,g,b=[c*255 for c in colorsys.hls_to_rgb(v[0]/360.,v[2]/100.,v[1]/100.)]
    elif "Gray" in t: r=g=b=v[0]/100.*255
    elif "CMYK" in t:
        c,m,y,k=[x/100. for x in v[:4]]; r=255*(1-c)*(1-k); g=255*(1-m)*(1-k); b=255*(1-y)*(1-k)
    else: r,g,b=v[0],v[1],v[2]
    return "#%02X%02X%02X"%(int(round(r)),int(round(g)),int(round(b)))
aprx=arcpy.mp.ArcGISProject(WORK)
col=aprx.listMaps("Map")[0].listLayers("deeplab_50a.tif")[0].getDefinition('V3').colorizer
ratcol={}
for g in col.groups:
    for c in g.classes: ratcol[str(c.values[0])]=cim_hex(c.color)
ratcol["Tree"]=TREE_NEW; ratcol["Grass"]=GRASS_NEW; ratcol["Road"]="#000000"; ratcol["Shadow-Noise"]="#343434"; ratcol["Bare Soil"]=BARE_NEW
counts={}
try:
    with arcpy.da.SearchCursor(CLASSIFIED_FULL,["Value","Count"]) as cur:
        for v,cnt in cur: counts[int(v)]=int(cnt)
except Exception:
    a=arcpy.RasterToNumPyArray(CLASSIFIED_FULL,nodata_to_value=0)
    for v in range(1,8): counts[v]=int((a==v).sum())
cellw=arcpy.Raster(CLASSIFIED_FULL).meanCellWidth
areas={v:counts.get(v,0)*cellw*cellw for v in range(1,8)}; tot_area=sum(areas.values()) or 1.0
pct={v:areas[v]/tot_area*100 for v in range(1,8)}
ther_full=arcpy.RasterToNumPyArray(arcpy.Raster(THERMAL_FULL),nodata_to_value=np.nan).astype("float32")

ELEV=LinearSegmentedColormap.from_list("elev",["#3B4248","#8C9094","#C3B488","#E8DFC2","#F7F1DE"])  # (v12b) neutral slate low end (not vegetation-green)
INF=plt.get_cmap("inferno")

def bez(p0,p1,p2,p3,n=48):
    t=np.linspace(0,1,n)[:,None]
    return ((1-t)**3)*p0+3*((1-t)**2)*t*p1+3*(1-t)*(t**2)*p2+(t**3)*p3
def zone_mask(poly, feather_m, coarse=4):
    nr,nc=NR//coarse,NC//coarse
    xs=(np.arange(nc)+0.5)/nc; ys=(np.arange(nr)+0.5)/nr; gx,gy=np.meshgrid(xs,ys)
    ins=MPath(poly).contains_points(np.column_stack([gx.ravel(),gy.ravel()])).reshape(nr,nc).astype("float32")
    ins=gaussian_filter(ins,(feather_m/CELL)/coarse)
    return np.clip(zoom(ins,(NR/nr,NC/nc),order=1)[:NR,:NC],0,1)
nd_poly=[(0,0),(ND_AX,0)]+[tuple(p) for p in bez(np.array([ND_AX,0]),np.array([ND_AX*0.92,ND_BY*0.30]),np.array([ND_AX*0.30,ND_BY*0.62]),np.array([0,ND_BY]))]+[(0,ND_BY)]
th_poly=[(1,1),(TH_BX,1)]+[tuple(p) for p in bez(np.array([TH_BX,1]),np.array([TH_BX+(1-TH_BX)*0.08,1-(1-TH_CY)*0.30]),np.array([TH_BX+(1-TH_BX)*0.70,TH_CY+(1-TH_CY)*0.55]),np.array([1,TH_CY]))]+[(1,TH_CY)]
alpha_nd=zone_mask(nd_poly,FEATHER_M)*np.where(np.isnan(ndsm),0.,1.)
alpha_th=zone_mask(th_poly,FEATHER_M)*np.where(np.isnan(ther),0.,1.)

ndn=np.nan_to_num(np.clip((ndsm-ND_RANGE[0])/(ND_RANGE[1]-ND_RANGE[0]),0,1)); elev_rgb=ELEV(ndn)[...,:3]
fin=np.isfinite(hs); hlo,hhi=np.percentile(hs[fin],2),np.percentile(hs[fin],98)
shade=np.clip((np.nan_to_num(hs,nan=hlo)-hlo)/max(hhi-hlo,1e-6),0,1)
elev_rgb=np.clip(elev_rgb*(ND_FLOOR+(1.0-ND_FLOOR)*shade[...,None]),0,1)
rgba_nd=np.dstack([elev_rgb,alpha_nd]).astype("float32")
thn=np.nan_to_num(np.clip((ther-TH_RANGE[0])/(TH_RANGE[1]-TH_RANGE[0]),0,1))
_thr=INF(thn)[...,:3].astype("float32")
if TH_HS_DARK>0 or TH_HS_LITE>0:
    _mt=2.0*shade-1.0; _relt=(1.0+np.where(_mt<0,TH_HS_DARK,TH_HS_LITE)*_mt)[...,None]
    _thr=np.clip(_thr*_relt,0,1)
rgba_th=np.dstack([_thr,alpha_th*TH_ZONE_ALPHA]).astype("float32")

try: fm.fontManager.addfont(r"C:\Windows\Fonts\arial.ttf"); plt.rcParams["font.family"]="Arial"
except Exception: pass
plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["pdf.fonttype"]=42; plt.rcParams["ps.fonttype"]=42   # (v12a) embed TrueType -> fixes Greek glyphs (e.g. iota) in PDF
HALO =[pe.Stroke(linewidth=2.4,foreground="#222222"),pe.Normal()]
HALOW=[pe.Stroke(linewidth=2.4,foreground="white"),pe.Normal()]

fig=plt.figure(figsize=(FIGW,FIGH),dpi=200); fig.patch.set_facecolor("white")
MAP_H=(MAP_W*FIGW/ASP)/FIGH; MAP_Y=MAP_TOP-MAP_H; MAP=[MAP_X,MAP_Y,MAP_W,MAP_H]
def mf(fx,fy): return (MAP_X+fx*MAP_W, MAP_Y+fy*MAP_H)
LENS_FRAC["Building"]=(0.26, (LENS_R*FIGW/FIGH)/MAP_H)

ax=fig.add_axes(MAP); ax.set_xlim(X0,X1); ax.set_ylim(Y0,Y1); ax.set_aspect("equal")
# (8.4) shaded-relief via BIDIRECTIONAL multiply: darken shadows + lift highlights -> keeps colour AND texture
shade_c=zoom(shade,(classified.shape[0]/NR,classified.shape[1]/NC),order=1); _m=2.0*shade_c-1.0
relief=(1.0+np.where(_m<0,RELIEF_DARK,RELIEF_LITE)*_m)[...,None]
classified_sr=classified.copy(); classified_sr[...,:3]=np.clip(classified[...,:3]*relief,0,1)
# (v11) roof hillshade boost: stronger relief on Building (#FF0000) so roofs keep texture
if ROOF_DARK>0 or ROOF_LITE>0:
    _bo=hx(RED_NEW); _bm=np.abs(classified[...,:3]-_bo).sum(2)<0.05
    _rrel=(1.0+np.where(_m<0,ROOF_DARK,ROOF_LITE)*_m)[...,None]
    _bst=np.clip(classified[...,:3]*_rrel,0,1)
    for _k in range(3): classified_sr[...,_k][_bm]=_bst[...,_k][_bm]
ax.imshow(classified_sr,extent=[X0,X1,Y0,Y1],origin="upper",zorder=1,alpha=CLASSIFIED_ALPHA)
# (8.1) light road overlay -> darker than Shadow #343434 but NOT pure black
_ro=hx("#000000"); _rm=np.abs(classified[...,:3]-_ro).sum(2)<0.05
_rr=np.zeros((classified.shape[0],classified.shape[1],4),dtype="float32"); _rr[...,3]=np.where(_rm,ROAD_ALPHA,0.0)
ax.imshow(_rr,extent=[X0,X1,Y0,Y1],origin="upper",zorder=1.3,interpolation="nearest")
ax.imshow(rgba_nd,extent=[X0,X1,Y0,Y1],origin="upper",zorder=2,interpolation="bilinear")
ax.imshow(rgba_th,extent=[X0,X1,Y0,Y1],origin="upper",zorder=3,interpolation="bilinear")
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color(NAVY); s.set_linewidth(1.2)
sw=X1-X0; sh=Y1-Y0
gx0=math.ceil(X0/GRID_STEP)*GRID_STEP; gy0=math.ceil(Y0/GRID_STEP)*GRID_STEP
xv=gx0
while xv<X1:
    ax.plot([xv,xv],[Y0,Y1],color="white",alpha=0.40,lw=0.6,zorder=4)
    ax.text(xv,Y0+sh*0.010,format(int(xv),","),color="white",fontsize=8.5,ha="center",va="bottom",rotation=90,zorder=6,path_effects=HALO); xv+=GRID_STEP
yv=gy0
while yv<Y1:
    ax.plot([X0,X1],[yv,yv],color="white",alpha=0.40,lw=0.6,zorder=4)
    ax.text(X0+sw*0.004,yv,format(int(yv),","),color="white",fontsize=8.5,ha="left",va="center",zorder=6,path_effects=HALO); yv+=GRID_STEP

def gr10(val): return format(int(round(val/10.0)*10),",").replace(",",".")

# class example labels inside the map
Hc,Wc=classified.shape[:2]
def msk(hexc,tol=0.07): o=hx(hexc); return (np.abs(classified[...,:3]-o).sum(2)<tol)
def pt_from_mask(m):
    if m.sum()<10: return None
    if m.sum()<60: ys,xs=np.where(m); r,c=int(np.median(ys)),int(np.median(xs))
    else: d=distance_transform_edt(m); r,c=np.unravel_index(int(np.argmax(d)),d.shape)
    return (X0+(c+0.5)/Wc*sw, Y1-(r+0.5)/Hc*sh)
AREA={5,6,7}; AREA_DARK={6:"#4A2D20",5:"#2E5A1E",7:"#1F1F1F"}
LABEL_CFG={5:dict(fs=11,step=0.016),6:dict(fs=13,step=0.019,dx=0.085,dy=0.045),7:dict(fs=7,step=0.011,dx=-0.0109,dy=-0.00276)}   # (v12a) Shadow label: 0.1cm lower into grey + one font size smaller
def gup(s):
    s=s.upper(); return "".join(c for c in unicodedata.normalize("NFD",s) if unicodedata.category(c)!="Mn")
def tracked(s): return "\u2009".join(list(s))
def label_orientation(m):  # (8.4) principal axis of the class mass via PCA, clamped
    ys,xs=np.where(m)
    if len(xs)<25: return 0.0
    pts=np.column_stack([xs.astype(float),ys.astype(float)])
    if len(pts)>20000: pts=pts[np.random.RandomState(0).choice(len(pts),20000,replace=False)]
    pts=pts-pts.mean(0); w,vec=np.linalg.eigh(np.cov(pts.T)); pc=vec[:,int(np.argmax(w))]
    a=math.degrees(math.atan2(-pc[1],pc[0]))
    if a>90: a-=180
    if a<-90: a+=180
    return max(-LABEL_MAX_TILT,min(LABEL_MAX_TILT,a))
def curved_label(cx,cy,text,ang_deg,color,step_m,bow_frac=0.14,fs=13):  # (8.4) chars along a gentle smile arc
    n=len(text)
    if n==0: return
    ang=math.radians(ang_deg); half=(n-1)/2.0; span=max(half*step_m,1e-6); curv=bow_frac/span
    ca,sa=math.cos(ang),math.sin(ang)
    for i,ch in enumerate(text):
        u=(i-half)*step_m; wv=curv*u*u; rot=ang_deg+math.degrees(math.atan(2*curv*u))   # smile: ends up, centre low
        px=cx+u*ca-wv*sa; py=cy+u*sa+wv*ca
        ax.text(px,py,ch,color=color,fontsize=fs,fontstyle="italic",ha="center",va="center",
                rotation=rot,rotation_mode="anchor",zorder=6,path_effects=HALOW)
for v,nm in MAP_LABEL.items():
    m=msk(CLS_HEX[v]); p=pt_from_mask(m)
    if not p: continue
    if v in AREA:
        cfg=LABEL_CFG.get(v,{}); px=p[0]+cfg.get("dx",0.0)*sw; py=p[1]+cfg.get("dy",0.0)*sh
        curved_label(px,py,gup(nm),label_orientation(m),AREA_DARK.get(v,"#333"),sw*cfg.get("step",LABEL_STEP_FRAC),fs=cfg.get("fs",13))
    else:
        ax.text(p[0],p[1],nm,color="white",fontsize=10.5,fontweight="bold",ha="center",va="center",zorder=6,path_effects=HALO)
mb=msk(RED_NEW); reg=np.zeros_like(mb); reg[int(Hc*0.55):,:int(Wc*0.32)]=mb[int(Hc*0.55):,:int(Wc*0.32)]
pb=pt_from_mask(reg)
if pb: ax.text(pb[0],pb[1],"Κτίρια",color="white",fontsize=10.5,fontweight="bold",ha="center",va="center",zorder=6,path_effects=HALO)

# scale bar 100 m centred, semi-transparent, raised
seg=20.0; nseg=5; total=seg*nseg
sx=(X0+X1)/2.0-total/2.0; sy=Y0+sh*0.085; bh=sh*0.012
for j in range(nseg):
    fc=to_rgba("white" if j%2==0 else NAVY, 0.80)
    ax.add_patch(Rectangle((sx+j*seg,sy),seg,bh,facecolor=fc,edgecolor=to_rgba(NAVY,0.9),lw=0.8,zorder=7))
for j in range(nseg+1): ax.text(sx+j*seg,sy-sh*0.006,str(int(j*seg)),color="white",fontsize=8.5,ha="center",va="top",zorder=7,path_effects=HALO)
ax.text(sx+total+sw*0.006,sy+bh/2,"m",color="white",fontsize=9,ha="left",va="center",zorder=7,path_effects=HALO)
# north top-right
nx=X1-sw*0.05; nyb=Y1-sh*0.20; nyt=Y1-sh*0.07
ax.annotate("",xy=(nx,nyt),xytext=(nx,nyb),arrowprops=dict(arrowstyle="-|>",color="white",lw=3.0,path_effects=[pe.Stroke(linewidth=5,foreground="#222"),pe.Normal()]),zorder=8)
ax.text(nx,nyt+sh*0.012,"Β",color="white",fontsize=15,fontweight="bold",ha="center",va="bottom",zorder=8,path_effects=HALO)

ov=fig.add_axes([0,0,1,1]); ov.set_xlim(0,1); ov.set_ylim(0,1); ov.axis("off"); ov.patch.set_alpha(0); ov.set_zorder(10)
def fpos(dx,dy): return fig.transFigure.inverted().transform(ax.transData.transform((dx,dy)))

for L in meta["lenses"]:
    # (1) lens footprint is a CIRCLE (matches the round lens view), leader to its edge
    en=L["name_en"]; lx,ly=mf(*LENS_FRAC[en]); half=L["ground_m"]/2.0
    ofx,ofy=fpos(L["cx"],L["cy"]); rfx=abs(fpos(L["cx"]+half,L["cy"])[0]-ofx)
    dxn,dyn=lx-ofx,ly-ofy; dd=math.hypot(dxn,dyn) or 1.0; tx,ty=ofx+dxn/dd*rfx, ofy+dyn/dd*rfx
    ov.plot([lx,tx],[ly,ty],color="white",lw=2.6,zorder=11); ov.plot([lx,tx],[ly,ty],color=NAVY,lw=1.2,zorder=11)
    ax.add_patch(Circle((L["cx"],L["cy"]),half,fill=False,edgecolor="white",lw=2.6,zorder=5))
    ax.add_patch(Circle((L["cx"],L["cy"]),half,fill=False,edgecolor=NAVY,lw=1.1,zorder=5))
    la=fig.add_axes([lx-LENS_R,ly-LENS_R*FIGW/FIGH,2*LENS_R,2*LENS_R*FIGW/FIGH]); la.axis("off"); la.set_zorder(13)
    im=la.imshow(mpimg.imread(os.path.join(OUT,L["png"])))
    circ=Circle((0.5,0.5),0.5,transform=la.transAxes,facecolor="none",edgecolor="white",lw=4,zorder=14); la.add_patch(circ); im.set_clip_path(circ)
    la.add_patch(Circle((0.5,0.5),0.5,transform=la.transAxes,facecolor="none",edgecolor=NAVY,lw=1.4,zorder=15))
    pr_w=2*LENS_R*FIGW*0.0254; scale=int(round(L["ground_m"]/pr_w/10.)*10)
    la.text(0.5,0.845,"1:%d"%scale,transform=la.transAxes,ha="center",va="center",fontsize=8.5,fontweight="bold",color="white",zorder=16,path_effects=HALO)
    s=LENS_EL.get(en,""); span=len(s)*10.5; ang=np.linspace(270-span/2,270+span/2,len(s)) if len(s)>1 else [270.0]
    for ch,a in zip(s,ang):
        rad=math.radians(a); xx=0.5+0.40*math.cos(rad); yy=0.5+0.40*math.sin(rad)
        la.text(xx,yy,ch,transform=la.transAxes,ha="center",va="center",fontsize=10,fontweight="bold",color="white",rotation=a-270.0,rotation_mode="anchor",zorder=16,path_effects=HALO)

def faint_wash(x,y,w,h): ov.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.004,rounding_size=0.010",mutation_aspect=R,facecolor="white",alpha=0.20,edgecolor="none",zorder=10))
def style_hist(a,title):
    a.set_title(title,fontsize=9,color=NAVY,fontweight="bold",pad=2,path_effects=HALOW)
    a.set_yticks([]); a.tick_params(length=0)
    for lbl in a.get_xticklabels(): lbl.set_color("white"); lbl.set_fontsize(7.5); lbl.set_path_effects(HALO)
    for s in a.spines.values(): s.set_visible(False)
    a.patch.set_alpha(0)
HW=0.082; HH=0.044
g0=math.ceil(X0/GRID_STEP)*GRID_STEP
def fcx_of(meter): return (meter-X0)/sw
fcx_nd=fcx_of(g0+50.0); fcx_th=fcx_of(g0+50.0+300.0)
def place(fcx,fy_b):
    return (MAP_X+fcx*MAP_W-HW/2.0, MAP_Y+fy_b*MAP_H)
hxx,hyy=place(fcx_nd,0.915); faint_wash(hxx-0.012,hyy-0.006,HW+0.024,HH+0.030)
axh=fig.add_axes([hxx,hyy,HW,HH]); axh.set_zorder(12)
nv=ndsm[np.isfinite(ndsm)]; cn,ed=np.histogram(nv,bins=16,range=(ND_RANGE[0],ND_RANGE[1])); ct=(ed[:-1]+ed[1:])/2
axh.bar(ct,cn,width=(ed[1]-ed[0])*0.92,color=ELEV((ct-ND_RANGE[0])/(ND_RANGE[1]-ND_RANGE[0])),edgecolor="white",linewidth=0.3)
axh.set_xticks([0,10,20]); style_hist(axh,"Ύψος nDSM (m)")
hxx,hyy=place(fcx_th,0.020); faint_wash(hxx-0.012,hyy-0.006,HW+0.024,HH+0.030)
axt=fig.add_axes([hxx,hyy,HW,HH]); axt.set_zorder(12)
tv=ther_full[np.isfinite(ther_full)]; cn2,ed2=np.histogram(tv,bins=16,range=(TH_RANGE[0],TH_RANGE[1])); ct2=(ed2[:-1]+ed2[1:])/2
axt.bar(ct2,cn2,width=(ed2[1]-ed2[0])*0.92,color=INF((ct2-TH_RANGE[0])/(TH_RANGE[1]-TH_RANGE[0])),edgecolor="white",linewidth=0.3)
axt.set_xticks([20,40,60]); style_hist(axt,"Θερμικό (°C)")

# ===================== RIGHT WHITE COLUMN (flowing layout) =====================
LX=0.738; LTX=0.764; RR=0.985; LBAR0=0.882; LBARW=0.072
swx=0.013; swy=swx*FIGW/FIGH
def hline(y): ov.plot([LX,RR],[y,y],color="#cfcfcf",lw=0.8,zorder=11)

iw2=0.150
if os.path.exists(INSET) and os.path.exists(INSET_META):
    mi=json.load(open(INSET_META)); IX0,IX1,IY0,IY1=mi["extent"]; SX,SY=mi["star"]
    ins=mpimg.imread(INSET); Hh=ins.shape[0]; cut=int(Hh*0.13); ins=ins[:Hh-cut,:,:]; IY0n=IY0+0.13*(IY1-IY0)
    ih2=iw2*FIGW/FIGH*(ins.shape[0]/ins.shape[1]); icx=(LX+RR)/2.0; itop=MAP_TOP
    fig.text(icx,itop+0.010,"Θέση περιοχής — Λέσβος",ha="center",fontsize=11,color=NAVY,fontweight="bold")
    ai=fig.add_axes([icx-iw2/2,itop-ih2,iw2,ih2]); im=ai.imshow(ins,extent=[IX0,IX1,IY0n,IY1],aspect="auto")
    ai.set_xlim(IX0,IX1); ai.set_ylim(IY0n,IY1); ai.set_xticks([]); ai.set_yticks([])
    for s in ai.spines.values(): s.set_visible(False)
    rb=FancyBboxPatch((0,0),1,1,transform=ai.transAxes,boxstyle="round,pad=0,rounding_size=0.06",mutation_aspect=(iw2*FIGW)/(ih2*FIGH),facecolor="none",edgecolor="#999",linewidth=1.0,zorder=12,clip_on=False)
    ai.add_patch(rb); im.set_clip_path(rb)
    ai.plot([SX],[SY],marker="*",ms=15,mfc="#E60000",mec="white",mew=1.0,zorder=8)
    ai.text(SX,SY,"  Περιοχή μελέτης",ha="left",va="center",fontsize=7.5,color="#111",zorder=9,path_effects=HALOW)
    ai.text(0.28,0.66,"ΛΕΣΒΟΣ",transform=ai.transAxes,ha="center",fontsize=9,color="#444",fontweight="bold",zorder=9)
    h2=[pe.Stroke(linewidth=2.2,foreground="white"),pe.Normal()]
    latc=math.degrees(2*math.atan(math.exp(((IY0+IY1)/2)/6378137))-math.pi/2); cosf=math.cos(math.radians(latc))
    iwid=IX1-IX0; ihei=IY1-IY0n; segkm=20; nsg=5; segm=segkm*1000.0/cosf
    bxx=IX0+iwid*0.07; byy=IY0n+ihei*0.10; bhh=ihei*0.026
    for j in range(nsg): ai.add_patch(Rectangle((bxx+j*segm,byy),segm,bhh,facecolor=("black" if j%2==0 else "white"),edgecolor="black",lw=0.6,zorder=9))
    for j in range(nsg+1): ai.text(bxx+j*segm,byy-ihei*0.018,str(j*segkm),ha="center",va="top",fontsize=6,color="#111",zorder=9,path_effects=h2)
    ai.text(bxx+nsg*segm+iwid*0.015,byy+bhh/2,"km",ha="left",va="center",fontsize=6,color="#111",zorder=9,path_effects=h2)
    nX=IX1-iwid*0.08; nY=IY1-ihei*0.22
    ai.annotate("",xy=(nX,nY+ihei*0.14),xytext=(nX,nY),arrowprops=dict(arrowstyle="-|>",color="black",lw=1.5),zorder=9)
    ai.text(nX,nY+ihei*0.16,"Β",ha="center",va="bottom",fontsize=8,fontweight="bold",color="#111",zorder=9,path_effects=h2)
    ins_bottom=itop-ih2
else:
    ins_bottom=MAP_TOP-0.18

cy=ins_bottom-0.014; hline(cy)
cy-=0.022
fig.text(LX,cy,"Υπόμνημα ταξινόμησης · Κάλυψη ανά κλάση (%)",fontsize=11,color=NAVY,fontweight="bold",ha="left",va="center")
cy-=0.026
# (8.5) legend swatches = textured material samples (class colour x real hillshade relief, same pipeline as the map)
_anc=zoom(alpha_nd,(classified.shape[0]/NR,classified.shape[1]/NC),order=1)
_atc=zoom(alpha_th,(classified.shape[0]/NR,classified.shape[1]/NC),order=1)
_central=(_anc<0.15)&(_atc<0.15)
_TH,_TW=46,128
def _ctile(v):
    m=msk(CLS_HEX[v])&_central
    if int(m.sum())<_TH*_TW*3: m=msk(CLS_HEX[6])&_central
    d=distance_transform_edt(m); r0,c0=np.unravel_index(int(np.argmax(d)),d.shape)
    r0=int(np.clip(r0,_TH//2,shade_c.shape[0]-_TH//2)); c0=int(np.clip(c0,_TW//2,shade_c.shape[1]-_TW//2))
    return shade_c[r0-_TH//2:r0+_TH//2,c0-_TW//2:c0+_TW//2]
def swatch_tile(v):
    t=_ctile(v); mt=2.0*t-1.0
    if v==2 and (ROOF_DARK>0 or ROOF_LITE>0): rel=1.0+np.where(mt<0,ROOF_DARK,ROOF_LITE)*mt
    else: rel=1.0+np.where(mt<0,RELIEF_DARK,RELIEF_LITE)*mt
    C=hx(CLS_HEX[v]); tile=np.clip(C[None,None,:]*rel[...,None],0,1); tile=CLASSIFIED_ALPHA*tile+(1.0-CLASSIFIED_ALPHA)
    if v==3: tile=(1.0-ROAD_ALPHA)*tile
    return tile
SWT={}; WASH={}
for _v in range(1,8):
    _t=swatch_tile(_v); SWT[_v]=_t; _rgb=_t.reshape(-1,3).mean(0)
    WASH[_v]="#%02X%02X%02X"%tuple(int(round(x*255)) for x in np.clip(_rgb,0,1))
order=sorted(range(1,8),key=lambda v:-areas[v]); maxp=max(pct.values())
dyr=0.021; barh=0.013; sww=0.020; swh=0.012; rowtop=cy
for i,v in enumerate(order):
    y=rowtop-i*dyr
    sa=fig.add_axes([LX,y-swh/2,sww,swh]); sa.imshow(SWT[v],aspect="auto"); sa.set_xticks([]); sa.set_yticks([])
    for _s in sa.spines.values(): _s.set_edgecolor("#333"); _s.set_linewidth(0.6)
    ov.text(LTX,y,"%s (%s)"%(CLS_NAME[v],CLS_EN[v]),va="center",ha="left",fontsize=9.5,color="#222",zorder=12)
    ov.add_patch(Rectangle((LBAR0,y-barh/2),max(LBARW*pct[v]/maxp,0.0015),barh,facecolor=WASH.get(v,ratcol.get(CLS_EN[v],"#888")),edgecolor="#555",lw=0.5,zorder=12))
    ov.text(LBAR0+LBARW*pct[v]/maxp+0.004,y,"%.1f%%"%pct[v],va="center",ha="left",fontsize=8.5,color=NAVY,fontweight="bold",zorder=12)
cy=rowtop-6*dyr-0.018; hline(cy)
cy-=0.024
ov.plot([LX+swx/2],[cy],marker="o",ms=12,mfc="white",mec=NAVY,mew=1.6,zorder=12)
ov.text(LTX,cy+0.008,"Μεγεθυντικός φακός — λεπτομέρεια RGB",va="center",ha="left",fontsize=9,color="#222",zorder=12)
ov.text(LTX,cy-0.010,"(φυσικό χρώμα) σε επιλεγμένες θέσεις",va="center",ha="left",fontsize=9,color="#222",zorder=12)
cy-=0.026; hline(cy)

def ramp(x,y,w,h,cmap,vmin,vmax,title,ticks):
    a=fig.add_axes([x,y,w,h]); a.imshow(np.linspace(0,1,256)[None,:],aspect="auto",cmap=cmap,extent=[vmin,vmax,0,1])
    a.set_yticks([]); a.set_xticks(ticks); a.tick_params(labelsize=8.5,length=3,color="#666")
    for s in a.spines.values(): s.set_color("#999"); s.set_linewidth(0.5)
    fig.text(x,y+h+0.006,title,fontsize=10,color=NAVY,fontweight="bold",ha="left",va="bottom")
cy-=0.040; ramp(LX,cy,RR-LX,0.018,ELEV,0,25,"Ύψος nDSM (m)",[0,5,10,15,20,25])
cy-=0.052; ramp(LX,cy,RR-LX,0.018,INF,TH_RANGE[0],TH_RANGE[1],"Θερμοκρασία (°C)",[20,30,40,50,60])
cy-=0.028; hline(cy)

rf=int(round(((X1-X0)/(MAP_W*FIGW*0.0254))/100.0)*100); wkm=int(round((X1-X0)/10.0)*10); hkm=int(round((Y1-Y0)/10.0)*10)
info=["Περιοχή: Πάμφιλα, Μυτιλήνη (Λέσβος)",
      "Αισθητήρας: MicaSense Altum-PT  ·  Λήψη: Σεπτέμβριος 2025",
      "Μοντέλο: DeepLabV3 + PointRend (ResNet-101, 7-Band)",
      "Ανάλυση εδάφους (GSD): 4,52 cm  ·  Μονάδες: μέτρα (m)",
      "Σύστημα αναφοράς: EPSG:32635 (UTM 35N)  ·  Κάνναβος: 100 m",
      "Έκταση περιοχής: ≈ %d m (Α–Δ) × %d m (Β–Ν)"%(wkm,hkm),
      "Γωνίες: ΒΔ %s, %s  ·  ΝΑ %s, %s"%(gr10(X0),gr10(Y1),gr10(X1),gr10(Y0)),
      "Κλίμακα ≈ 1:%s"%format(rf,",").replace(",","."),
      "Πηγή: RSGIS Lab, Τμήμα Γεωγραφίας, Πανεπιστήμιο Αιγαίου",
      "Επιβλέπων: Δρ. Χρ. Βασιλάκος  ·  Δημιουργός: Ν. Κορωνιάδης",
      "Τελευταία ενημέρωση: Ιούνιος 2026"]
cy-=0.022; fig.text(LX,cy,"Στοιχεία χάρτη",fontsize=11.5,color=NAVY,fontweight="bold",va="center")
cy-=0.024
for txt in info:
    fig.text(LX,cy,txt,fontsize=9.5,color="#333",ha="left",va="center"); cy-=0.0205

fig.text(MAP_X+MAP_W/2,0.955,"Σύνθετος Χάρτης Κάλυψης Γης — Πάμφιλα, Μυτιλήνη (Λέσβος)",ha="center",va="center",fontsize=24,color=NAVY,fontweight="bold")

LSQ=1.0; lbw=LSQ/FIGW; lbh=LSQ/FIGH
if os.path.exists(EMB):
    a=fig.add_axes([0.010,0.975-lbh,lbw,lbh]); a.axis("off"); a.imshow(mpimg.imread(EMB))
if os.path.exists(QR):
    # (v12b+) QR linking to the live web app, placed in the bottom-left margin BELOW the map
    qs=0.78; qw=qs/FIGW; qh=qs/FIGH; qx=0.012; qy=0.006
    ov.add_patch(Rectangle((qx-0.003,qy-0.003),qw+0.006,qh+0.006,fill=False,edgecolor=NAVY,lw=1.4,zorder=11))
    a=fig.add_axes([qx,qy,qw,qh]); a.axis("off"); a.imshow(mpimg.imread(QR))
    cxq=qx+qw+0.008
    fig.text(cxq,qy+qh*0.66,"Map Creation",fontsize=8.5,fontweight="bold",color=NAVY,ha="left",va="center")
    fig.text(cxq,qy+qh*0.30,"σάρωσε → διαδραστική παρουσίαση",fontsize=6.6,color="#555",ha="left",va="center")
RH=0.60; rh=RH/FIGH
if os.path.exists(DLOGO):
    dw=RH/FIGW*(384/123); a=fig.add_axes([0.988-dw,0.975-rh,dw,rh]); a.axis("off"); a.imshow(mpimg.imread(DLOGO))
if os.path.exists(RSGIS):
    rw=RH/FIGW*(650/152); a=fig.add_axes([0.988-rw,0.018,rw,rh]); a.axis("off"); a.imshow(mpimg.imread(RSGIS))

RUN_ID="v12b"
png=os.path.join(OUT,"Hero_Layout.png"); pdf=os.path.join(OUT,"Hero_Layout.pdf")
fig.savefig(png,dpi=300,facecolor="white"); fig.savefig(pdf,dpi=300,facecolor="white"); plt.close(fig)
# hyperparameter log (id matches the image filename suffix)
import datetime as _dt
_log=os.path.join(OUT,"compose_runs_log.txt")
_knobs=dict(GRASS_NEW=GRASS_NEW,BARE_NEW=BARE_NEW,TREE_NEW=TREE_NEW,CLASSIFIED_ALPHA=CLASSIFIED_ALPHA,
            RELIEF_DARK=RELIEF_DARK,RELIEF_LITE=RELIEF_LITE,ROAD_ALPHA=ROAD_ALPHA,ND_FLOOR=ND_FLOOR,
            TH_HS_DARK=TH_HS_DARK,TH_HS_LITE=TH_HS_LITE,ROOF_DARK=ROOF_DARK,ROOF_LITE=ROOF_LITE,
            RED_NEW=RED_NEW,TH_ZONE_ALPHA=TH_ZONE_ALPHA,SKIASI_dx=-0.0109,SKIASI_dy=-0.00276)
with open(_log,"a",encoding="utf-8") as _f:
    _f.write("[%s] id=%s\n"%(_dt.datetime.now().isoformat(timespec="seconds"),RUN_ID))
    _f.write("  png=%s\n  pdf=%s\n"%(os.path.basename(png),os.path.basename(pdf)))
    _f.write("  "+"  ".join("%s=%s"%(k,v) for k,v in _knobs.items())+"\n\n")
print("SAVED",png); print("LOG",_log); print("DONE")
