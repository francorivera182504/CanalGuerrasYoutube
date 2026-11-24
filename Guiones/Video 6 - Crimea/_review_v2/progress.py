import json,re
from pathlib import Path
from datetime import datetime
p=Path(__file__).resolve().parent
state=json.loads((p/'render_status.json').read_text(encoding='utf-8'))
print('Render:',state['status'])
log=(p/'render.log').read_text(encoding='utf-8',errors='replace')
parts={}
for sid,n,total in re.findall(r'seg(\d+): (\d+)/(\d+)',log):
    parts[int(sid)]=(int(n),int(total))
known=sum(total if sid+7 in parts or state['status']=='completed' else n for sid,(n,total) in parts.items())
elapsed=(datetime.now().astimezone()-datetime.fromisoformat(state['started'])).total_seconds()
print(f'Elapsed: {elapsed/60:.1f} min; logged progress >= {known}/12161 frames ({100*known/12161:.1f}%)')
print('Recent log:',*log.splitlines()[-5:],sep='\n')
if (p/'verification_status.json').exists():
    print((p/'verification_status.json').read_text(encoding='utf-8'))
