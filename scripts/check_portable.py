"""Verify project-local libraries from a temporary relocated copy on this PC."""
from pathlib import Path
import tempfile,shutil,subprocess,json
ROOT=Path(__file__).resolve().parents[1];NAME='ACT161_Frequency_Divider'
CLI=r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
results=[]
with tempfile.TemporaryDirectory(prefix='.portable_check_',dir=ROOT.parent) as temp:
    target=Path(temp).resolve()
    assert target.parent==ROOT.parent.resolve() and target.name.startswith('.portable_check_')
    for rel in [NAME+'.kicad_pro',NAME+'.kicad_sch',NAME+'.kicad_pcb','fp-lib-table','sym-lib-table']:
        shutil.copy2(ROOT/rel,target/rel)
    for rel in ['libraries',NAME+'.pretty']:shutil.copytree(ROOT/rel,target/rel)
    commands=[['sch','erc','--severity-all','--exit-code-violations','-o',str(ROOT/'reports'/'portable_ERC.txt'),str(target/(NAME+'.kicad_sch'))],['pcb','drc','--schematic-parity','--all-track-errors','--severity-all','--exit-code-violations','--refill-zones','-o',str(ROOT/'reports'/'portable_DRC.txt'),str(target/(NAME+'.kicad_pcb'))]]
    for args in commands:
        result=subprocess.run([CLI]+args,capture_output=True,text=True)
        results.append({'command':[CLI]+args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        print(result.stdout,flush=True)
(ROOT/'reports'/'portable_runs.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
assert all(r['exit_code']==0 for r in results),'Relocated copy has native violations'
print('Same-PC relocated copy: native ERC/DRC/parity PASS')
