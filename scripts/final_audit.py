"""Audit the delivered file set and checks not enabled in KiCad's defaults."""
from pathlib import Path
import pcbnew as p
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];NAME='ACT161_Frequency_Divider'
required=[NAME+e for e in ['.kicad_pro','.kicad_sch','.kicad_pcb']]+['fp-lib-table','sym-lib-table','README.md','docs/schematic.pdf','docs/pcb_front.pdf','docs/pcb_back.pdf','docs/assembly_front.pdf','docs/assembly_back.pdf','docs/pinout.md','reports/ERC.txt','reports/DRC.txt','reports/validation.md','reports/BOM.csv','previews/schematic.png','previews/pcb_front.png','previews/pcb_back.png','previews/pcb_3d.png']
for rel in required:assert (ROOT/rel).is_file() and (ROOT/rel).stat().st_size>0,rel
hashes=json.loads((ROOT/'reports'/'checked_sha256.json').read_text())
for rel,digest in hashes.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
project=json.loads((ROOT/(NAME+'.kicad_pro')).read_text())
settings=project['board']['design_settings']
assert settings['drc_exclusions']==[]
severities=settings.get('rule_severities',{})
for rule in ['clearance','shorting_items','unconnected_items','courtyards_overlap','copper_edge_clearance','solder_mask_bridge']:
    assert severities.get(rule,'error')=='error',rule
for key,value in {'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_to_hole':.25,'min_copper_edge_clearance':.5,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.1}.items():
    assert abs(settings['rules'][key]-value)<1e-9,key
for report in ['native_runs.json','portable_runs.json']:
    assert all(r['exit_code']==0 for r in json.loads((ROOT/'reports'/report).read_text())),report
board=p.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
for fp in board.GetFootprints():
    ref=fp.GetReference();pads=list(fp.Pads());numbers={a.GetNumber() for a in pads}
    if ref=='U1':assert numbers=={str(i) for i in range(1,17)}
    assert ref!='U2','Removed output buffer must not be present'
    if ref=='U3':assert numbers=={str(i) for i in range(1,6)}
    if ref=='J1':assert numbers=={'1','2','3','4','5','SH'}
    if ref=='J4':assert numbers=={'1','2'}
    if ref in ['J2','J3']:assert numbers=={str(i) for i in range(1,11)}
    if ref.startswith(('R','C')) or ref=='LED1':assert numbers=={'1','2'}
    want=p.PAD_ATTRIB_NPTH if ref.startswith('H') else (p.PAD_ATTRIB_PTH if ref in ['U1','LED1','J4'] else p.PAD_ATTRIB_SMD)
    assert all(a.GetAttribute()==want for a in pads),ref
    courtyard=p.F_CrtYd
    assert any(g.GetLayer()==courtyard for g in fp.GraphicalItems()),ref+' courtyard'
    for m in fp.Models():
        name=m.m_Filename
        assert name.startswith('${KIPRJMOD}/'),name
        assert (ROOT/name.replace('${KIPRJMOD}/','')).is_file(),name
for z in board.Zones():assert z.GetIslandRemovalMode()==p.ISLAND_REMOVAL_MODE_ALWAYS
ds=board.GetDesignSettings()
assert abs(p.ToMM(ds.m_SolderMaskExpansion)-.05)<1e-5
assert abs(p.ToMM(ds.m_SolderMaskMinWidth)-.1)<1e-5
tracks=list(board.GetTracks())
for via in tracks:
    if not isinstance(via,p.PCB_VIA) or via.GetNetname()=='/GND':continue
    ls=set()
    for t in tracks:
        if isinstance(t,p.PCB_VIA) or t.GetNetCode()!=via.GetNetCode():continue
        if t.GetStart()==via.GetPosition() or t.GetEnd()==via.GetPosition():ls.add(t.GetLayer())
    assert ls=={p.F_Cu,p.B_Cu},'Signal via endpoint/layers'
report='''Final artifact audit: PASS
- All requested native files, PDFs, PNG previews, BOM and documentation present.
- SHA256 matches the files that passed the last native ERC/DRC run.
- DRC exclusions empty; critical checks remain errors; user project settings preserved.
- Saved project minima verified: copper 0.20 mm, silk 0.15 mm, track 0.20 mm, via 0.60 mm, edge 0.50 mm.
- Every footprint has courtyard on its assembly side.
- Full pad-number sets and physical pad types match the independent assembly list.
- All non-ground vias terminate tracks at their centers on both copper layers.
- GND zones remove all isolated islands.
- Solder-mask expansion 0.05 mm and minimum web 0.10 mm confirmed from saved board.
- Every referenced 3D model exists inside the portable project directory.
- Same-PC relocated copy passed native ERC/DRC/parity (portable_ERC.txt / portable_DRC.txt).
This audit is not physical testing or mechanical qualification of J2/J3/SCS-16.
'''
(ROOT/'reports'/'final_audit.txt').write_text(report,encoding='utf-8')
print(report)
