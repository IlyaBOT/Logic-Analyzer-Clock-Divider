"""Independent function-table, netlist and physical pin-to-pad assertions."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json,math,unittest
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];NAME='ACT161_Frequency_Divider'
expected=json.loads((ROOT/'reports'/'expected_nets.json').read_text())

class Counter:
    def __init__(self):self.q=0;self.clk=0
    def drive(self,clk,clr=1,load=1,enp=1,ent=1,data=0):
        if not clr:self.q=0
        elif not self.clk and clk:
            if not load:self.q=data&15
            elif enp and ent:self.q=(self.q+1)&15
        self.clk=clk
        return self.q, bool(ent and self.q==15)

class LogicTests(unittest.TestCase):
    def test_all_states_controls_edges(self):
        for q in range(16):
            for clr in range(2):
                for load in range(2):
                    for enp in range(2):
                        for ent in range(2):
                            for data in range(16):
                                c=Counter();c.q=q
                                want=0 if not clr else (data if not load else ((q+1)&15 if enp and ent else q))
                                v,r=c.drive(1,clr,load,enp,ent,data)
                                self.assertEqual(v,want)
                                self.assertEqual(r,bool(ent and want==15))
                                self.assertEqual(c.drive(1,clr,load,enp,ent,data)[0],want,'steady high is not an edge')
                                self.assertEqual(c.drive(0,clr,load,enp,ent,data)[0],want,'falling edge must not count')
    def test_async_clear(self):
        for clk in [0,1]:
            c=Counter();c.q=15;c.clk=clk
            self.assertEqual(c.drive(clk,clr=0)[0],0)
    def test_binary_sequence_division_duty(self):
        c=Counter();seq=[]
        for n in range(256):
            seq.append(c.q);c.drive(1);c.drive(0)
        self.assertEqual(seq[:16],list(range(16)))
        for bit,div in enumerate([2,4,8,16]):
            wave=[(q>>bit)&1 for q in seq]
            rising=[i for i in range(1,256) if wave[i] and not wave[i-1]]
            self.assertTrue(all(b-a==div for a,b in zip(rising,rising[1:])))
            self.assertEqual(sum(wave),128)
    def test_startup_phase(self):
        for initial in range(16):
            c=Counter();c.q=initial;seq=[]
            for _ in range(16):seq.append(c.q);c.drive(1);c.drive(0)
            self.assertEqual(set(seq),set(range(16)))

def nets_xml():
    root=ET.parse(ROOT/'reports'/'netlist.xml').getroot();actual={}
    for n in root.find('nets'):
        name=n.attrib['name'].lstrip('/');nodes=sorted((a.attrib['ref'],a.attrib['pin']) for a in n.findall('node'))
        actual[name]=nodes
    return root,actual

class ElectricalTests(unittest.TestCase):
    def test_netlist_exact(self):
        _,actual=nets_xml()
        for name,nodes in expected.items():self.assertEqual(actual[name],sorted(tuple(n) for n in nodes),name)
        unexpected={k:v for k,v in actual.items() if k not in expected and not k.startswith('unconnected-')}
        self.assertEqual(unexpected,{})
    def test_datasheet_pinmaps(self):
        _,nets=nets_xml();by_pin={}
        for n,nodes in nets.items():
            for ref,num in nodes:by_pin[(ref,num)]=n
        u1={1:'VCC_LOGIC',2:'CLK_U1',3:'GND',4:'GND',5:'GND',6:'GND',7:'VCC_LOGIC',8:'GND',9:'VCC_LOGIC',10:'VCC_LOGIC',11:'Q16',12:'Q8',13:'Q4',14:'Q2',16:'VCC_LOGIC'}
        for pin,net in u1.items():self.assertEqual(by_pin['U1',str(pin)],net)
        self.assertFalse(any(ref=='U2' for ref,pin in by_pin))
        for pin,net in {1:'+5V',2:'GND',3:'+5V',5:'+3V3'}.items():self.assertEqual(by_pin['U3',str(pin)],net)
    def test_pass_isolation_and_alternative_power(self):
        _,nets=nets_xml()
        for pin in [2,4,6,8,10]:self.assertEqual(nets['PASS'+str(pin)],[('J2',str(pin)),('J3',str(pin))])
        self.assertFalse(any(r in ['J2','J3'] for r,pin in nets['+5V']))
        self.assertFalse(any(r in ['J2','J3'] for r,pin in nets['+3V3']))
        self.assertFalse(any(r in ['J2','J3'] for r,pin in nets['VCC_LOGIC']))
        self.assertIn(('J4','1'),nets['+5V'])
        self.assertIn(('J4','2'),nets['GND'])
    def test_direct_outputs_and_power_selection(self):
        _,nets=nets_xml()
        for i,d in enumerate([2,4,8,16],1):
            self.assertEqual(nets[f'Q{d}'],[('R'+str(i),'1'),('U1',str(15-i))])
            self.assertEqual(nets[f'DIV{d}'],[('J2',str(2*i-1)),('R'+str(i),'2')])
        self.assertIn(('R5','1'),nets['+5V']);self.assertIn(('R5','2'),nets['VCC_LOGIC'])
        self.assertIn(('R6','1'),nets['+3V3']);self.assertIn(('R6','2'),nets['VCC_LOGIC'])
    def test_all_footprints(self):
        xml,_=nets_xml()
        for c in xml.find('components'):
            lib,n=c.findtext('footprint').split(':')
            self.assertEqual(lib,NAME)
            self.assertTrue((ROOT/(NAME+'.pretty')/(n+'.kicad_mod')).exists())

class BoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board=p.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
        cls.fp={f.GetReference():f for f in cls.board.GetFootprints()}
    def test_exact_pad_nets(self):
        actual={}
        for ref,fp in self.fp.items():
            for pad in fp.Pads():
                name=pad.GetNetname().lstrip('/')
                if name and not name.startswith('unconnected-'):actual.setdefault(name,[]).append((ref,pad.GetNumber()))
        self.assertEqual({n:sorted(set(v)) for n,v in actual.items()},{n:sorted(tuple(x) for x in v) for n,v in expected.items()})
    def test_connector_sides_numbering(self):
        for ref,x in [('J2',128.7),('J3',167.3)]:
            pads={a.GetNumber():a for a in self.fp[ref].Pads()}
            self.assertEqual(len(pads),10)
            for i in range(5):
                for num,layer,other in [(2*i+1,p.F_Cu,p.B_Cu),(2*i+2,p.B_Cu,p.F_Cu)]:
                    a=pads[str(num)]
                    self.assertTrue(a.IsOnLayer(layer));self.assertFalse(a.IsOnLayer(other))
                    self.assertFalse(a.IsOnLayer(p.F_Paste));self.assertFalse(a.IsOnLayer(p.B_Paste))
                    self.assertEqual(a.GetAttribute(),p.PAD_ATTRIB_SMD)
                    self.assertAlmostEqual(p.ToMM(a.GetPosition().x),x,places=4)
                    self.assertAlmostEqual(p.ToMM(a.GetPosition().y),93.32+i*2.54,places=4)
            self.assertEqual(self.fp[ref].GetLayer(),p.F_Cu)
    def test_geometry_and_decoupling(self):
        self.assertEqual(self.board.GetCopperLayerCount(),2)
        self.assertAlmostEqual(p.ToMM(self.board.GetDesignSettings().GetBoardThickness()),1.6)
        for r in ['H1','H2','H3','H4']:
            a=next(iter(self.fp[r].Pads()));self.assertAlmostEqual(p.ToMM(a.GetDrillSize().x),3.2)
        def distance(r,n,c,m):
            a=next(a for a in self.fp[r].Pads() if a.GetNumber()==str(n)).GetPosition()
            b=next(a for a in self.fp[c].Pads() if a.GetNumber()==str(m)).GetPosition()
            return math.hypot(p.ToMM(a.x-b.x),p.ToMM(a.y-b.y))
        self.assertLess(distance('U1',16,'C1',1),2.8)
        edge=[s for s in self.board.GetDrawings() if s.GetLayer()==p.Edge_Cuts]
        pts=[pt for s in edge for pt in [s.GetStart(),s.GetEnd()]]
        self.assertAlmostEqual(p.ToMM(max(a.x for a in pts)-min(a.x for a in pts)),42.8)
        self.assertAlmostEqual(p.ToMM(max(a.y for a in pts)-min(a.y for a in pts)),27.6)
    def test_power_header_location_and_polarity(self):
        pads={a.GetNumber():a for a in self.fp['J4'].Pads()}
        self.assertEqual(set(pads),{'1','2'})
        for num,net in [('1','+5V'),('2','GND')]:
            self.assertEqual(pads[num].GetAttribute(),p.PAD_ATTRIB_PTH)
            self.assertEqual(pads[num].GetNetname().lstrip('/'),net)
            self.assertAlmostEqual(p.ToMM(pads[num].GetDrillSize().x),1)
        self.assertAlmostEqual(p.ToMM(pads['2'].GetPosition().y-pads['1'].GetPosition().y),2.54)
        self.assertGreater(p.ToMM(pads['1'].GetPosition().x),p.ToMM(self.fp['J1'].GetPosition().x))
        self.assertLess(p.ToMM(pads['1'].GetPosition().x),p.ToMM(self.fp['LED1'].GetPosition().x))
    def test_user_routing_and_placement_preserved(self):
        baseline=json.loads((ROOT/'reports'/'input_user_layout.json').read_text())
        actual={t.m_Uuid.AsString():t for t in self.board.GetTracks()}
        def xy(v):return [v.x,v.y]
        for old in baseline['tracks']:
            t=actual[old['uuid']]
            self.assertEqual(type(t).__name__,old['kind'])
            self.assertEqual(t.GetNetname(),old['net'])
            self.assertEqual(xy(t.GetStart()),old['start']);self.assertEqual(xy(t.GetEnd()),old['end'])
            self.assertEqual(int(t.GetLayer()),old['layer'])
            if isinstance(t,p.PCB_VIA):
                self.assertEqual(t.GetWidth(p.F_Cu),old['diameter']);self.assertEqual(t.GetDrill(),old['drill'])
            else:self.assertEqual(t.GetWidth(),old['width'])
        for ref,old in baseline['footprints'].items():
            fp=self.fp[ref]
            self.assertEqual(fp.m_Uuid.AsString(),old['uuid']);self.assertEqual(xy(fp.GetPosition()),old['position'])
            self.assertEqual(fp.GetOrientationDegrees(),old['orientation']);self.assertEqual(fp.GetValue(),old['value'])
        outline=[{'start':xy(g.GetStart()),'end':xy(g.GetEnd())} for g in self.board.GetDrawings() if g.GetLayer()==p.Edge_Cuts]
        self.assertEqual(sorted(outline,key=str),sorted(baseline['outline'],key=str))
    def test_default_level_assembly(self):
        self.assertFalse(self.fp['R5'].IsDNP())
        for ref in ['R6','U3','C4']:self.assertTrue(self.fp[ref].IsDNP())
        self.assertNotIn('U2',self.fp)
        self.assertEqual(self.fp['U1'].GetValue(),'CD74ACT161E')

if __name__=='__main__':
    unittest.main(verbosity=2)
