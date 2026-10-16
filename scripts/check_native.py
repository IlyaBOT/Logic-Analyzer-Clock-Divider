"""Run authoritative KiCad checks and retain real command exit statuses."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];NAME='ACT161_Frequency_Divider'
CLI=r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
cmds=[['sch','erc','--severity-all','--exit-code-violations','-o',str(ROOT/'reports'/'ERC.txt'),str(ROOT/(NAME+'.kicad_sch'))],['pcb','drc','--schematic-parity','--all-track-errors','--severity-all','--exit-code-violations','--refill-zones','--save-board','-o',str(ROOT/'reports'/'DRC.txt'),str(ROOT/(NAME+'.kicad_pcb'))]]
results=[]
for args in cmds:
    r=subprocess.run([CLI]+args,capture_output=True,text=True)
    results.append({'command':[CLI]+args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    print(r.stdout.strip());print('exit code:',r.returncode)
test=subprocess.run([sys.executable,str(ROOT/'scripts'/'validate.py')],capture_output=True,text=True)
(ROOT/'reports'/'tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
results.append({'command':[sys.executable,str(ROOT/'scripts'/'validate.py')],'exit_code':test.returncode})
print(test.stdout+test.stderr)
(ROOT/'reports'/'native_runs.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
if any(r['exit_code'] for r in results):sys.exit(1)
hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/(NAME+ext) for ext in ['.kicad_sch','.kicad_pcb','.kicad_pro']]}
(ROOT/'reports'/'checked_sha256.json').write_text(json.dumps(hashes,indent=2))
