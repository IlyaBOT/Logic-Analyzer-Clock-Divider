"""Export native KiCad plots, 3D renders and rendered PDF previews."""
from pathlib import Path
import os,subprocess,sys,json,math
from PIL import Image,ImageChops
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];NAME='ACT161_Frequency_Divider'
CLI=Path(r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe')
POP=Path(r'C:\Users\IlyaBOT\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
os.environ['KIPRJMOD']=str(ROOT)
def run(args):
    r=subprocess.run([str(CLI)]+[str(x) for x in args],capture_output=True,text=True)
    print(r.stdout.strip(),flush=True)
    if r.stderr:print(r.stderr,flush=True)
    if r.returncode:raise RuntimeError('Export failed: '+str(args))
def preview(pdf,name):
    dest=ROOT/'previews'/name
    subprocess.run([str(POP),'-scale-to','2400','-png','-singlefile',str(pdf),str(dest)],check=True)
    im=Image.open(str(dest)+'.png').convert('RGB')
    if name!='schematic':
        diff=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0))))
        box=diff.getbbox()
        if box:im=im.crop((max(0,box[0]-35),max(0,box[1]-35),min(im.width,box[2]+35),min(im.height,box[3]+35)))
        im.save(str(dest)+'.png')

if __name__=='__main__':
    sch=ROOT/(NAME+'.kicad_sch');pcb=ROOT/(NAME+'.kicad_pcb')
    run(['sch','export','pdf','-o',ROOT/'docs'/'schematic.pdf',sch])
    run(['sch','export','svg','-o',ROOT/'previews',sch])
    preview(ROOT/'docs'/'schematic.pdf','schematic')
    plots=[('pcb_front','F.Cu,Edge.Cuts',False,False),('pcb_back','B.Cu,Edge.Cuts',True,False),('assembly_front','F.Fab,F.Silkscreen,Edge.Cuts',False,True),('assembly_back','B.Fab,B.Silkscreen,Edge.Cuts',True,True)]
    for n,ls,mirror,assembly in plots:
        args=['pcb','export','pdf','--mode-single','--scale','3','--black-and-white','--exclude-value','--layers',ls,'-o',ROOT/'docs'/(n+'.pdf')]
        if mirror:args+=['--mirror']
        if assembly:args+=['--sketch-pads-on-fab-layers','--crossout-DNP-footprints-on-fab-layers']
        run(args+[pcb]);preview(ROOT/'docs'/(n+'.pdf'),n)
    run(['pcb','export','svg','--layers','F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts','--mode-multi','--page-size-mode','2','--exclude-drawing-sheet','-o',ROOT/'previews'/'layers',pcb])
    run(['pcb','render','--width','1800','--height','1100','--quality','high','--background','opaque','--rotate','-25,0,20','-o',ROOT/'previews'/'pcb_3d.png',pcb])
    run(['pcb','render','--width','1800','--height','1100','--quality','high','--background','opaque','--side','bottom','-o',ROOT/'previews'/'pcb_3d_back.png',pcb])
    b=p.LoadBoard(str(pcb));length={};count={}
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):count[t.GetNetname()]=count.get(t.GetNetname(),0)+1;continue
        name=t.GetNetname().lstrip('/');layer=b.GetLayerName(t.GetLayer())
        length.setdefault(layer,0);length[layer]+=p.ToMM(t.GetLength())
    edge=[g for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts];pts=[pt for g in edge for pt in [g.GetStart(),g.GetEnd()]]
    w=p.ToMM(max(v.x for v in pts)-min(v.x for v in pts));h=p.ToMM(max(v.y for v in pts)-min(v.y for v in pts))
    metric={'tracks_length_mm':length,'vias':sum(count.values()),'ground_vias':count.get('/GND',0),'signal_vias':sum(v for n,v in count.items() if n!='/GND'),'board_mm':[w,h,p.ToMM(b.GetDesignSettings().GetBoardThickness())],'min_trace_mm':min(p.ToMM(t.GetWidth()) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA))}
    (ROOT/'reports'/'routing_metrics.json').write_text(json.dumps(metric,indent=2))
    print(json.dumps(metric),flush=True)
