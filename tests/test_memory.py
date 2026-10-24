import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import uuid

BASE = Path(__file__).resolve().parent
PACKAGE = BASE.parent / 'package'
ROOT = BASE / ('verification-' + uuid.uuid4().hex[:10])
ROOT.mkdir()
SHARED = ROOT / 'Shared OneDrive'
SHARED.mkdir()
PS = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
checks = []

def command(script, *args, payload=None, ok=True):
    cmd = [PS, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script), *map(str, args)]
    result = subprocess.run(cmd, input=(json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    out = result.stdout.decode('utf-8-sig', errors='replace').strip()
    if ok and result.returncode:
        raise AssertionError(f'{cmd}\n{out}\n{result.stderr.decode(errors="replace")}')
    if not ok:
        assert result.returncode, f'Expected rejection: {cmd}'
        return result
    return json.loads(out) if out else None

def check(name, condition=True):
    assert condition, name
    checks.append(name)
    print('PASS', name, flush=True)

def install(name):
    home = ROOT / name
    home.mkdir()
    (home / 'hooks.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [{'type':'command','command':'echo unrelated-hook'}]}]}}), encoding='utf-8')
    (home / 'AGENTS.md').write_text('Existing user guidance.\n', encoding='utf-8')
    result = command(PACKAGE/'Install.ps1', '-SharedRoot', SHARED, '-CodexRoot', home, '-DeviceName', name)
    return home, home/'skills/onedrive-project-memory/scripts/memory.ps1', result

def invoke(env, action, *args, payload=None, ok=True):
    home, runtime, _ = env
    return command(runtime, '-ConfigPath', home/'shared-memory/config.json', '-Action', action, *args, payload=payload, ok=ok)

def hook(env, project, event='UserPromptSubmit', session='session-1', turn='turn-1', **extra):
    return invoke(env,'Hook',payload=dict(cwd=str(project),hook_event_name=event,session_id=session,turn_id=turn,prompt='Continue work',**extra))

def ticket(env, session='session-1', turn='turn-1'):
    for file in (env[0]/'shared-memory/tickets').glob('*.json'):
        data=json.loads(file.read_text('utf-8'))
        if data['session_id']==session and data['turn_id']==turn:
            return file
    raise AssertionError('Ticket missing')

A=install('PC-A'); B=install('PC-B')
check('Two installations have distinct persistent device IDs',A[2]['device_id']!=B[2]['device_id'])
PA=ROOT/'project A 采购'; PB=ROOT/'project B 采购'
PA.mkdir(); PB.mkdir()
for env, path in [(A,PA),(B,PB)]:
    invoke(env,'Bind','-ProjectPath',path,'-ProjectId','sap-purchasing')
check('Same project ID binds different local paths')
note=ROOT/'note.md'
note.write_text('# 经验\n\n已验证：跨电脑查询采购审批流程。\n\n## 进度\n下一步验证采购订单。\n',encoding='utf-8')
first=hook(A,PA)
check('Hook context contains current bound project and ticket','sap-purchasing' in first['hookSpecificOutput']['additionalContext'])
ta=ticket(A)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(lambda _:invoke(A,'Save','-Ticket',ta,'-NoteFile',note), range(3)))
records=SHARED/'projects/sap-purchasing/records'
check('Concurrent repeated saves of one turn create one immutable file',len(list(records.glob('*.md')))==1)
original=next(records.glob('*.md')); original_bytes=original.read_bytes()
second=hook(B,PB)
check('Other device automatically receives readable Chinese experience','跨电脑查询采购审批流程' in second['hookSpecificOutput']['additionalContext'])
invoke(B,'Save','-Ticket',ticket(B),'-NoteFile',note)
check('Same session and turn on two devices do not overwrite',len(list(records.glob('*.md')))==2 and original.read_bytes()==original_bytes)
hook(A,PA,session='session-2')
invoke(A,'Save','-Ticket',ticket(A,'session-2'),'-NoteFile',note)
check('Two concurrent conversations on one device remain separate',len(list(records.glob('*.md')))==3)
check('Saved checkpoint does not request another model turn',hook(A,PA,event='Stop')=={})
hook(A,PA,turn='skip-turn')
invoke(A,'Skip','-Ticket',ticket(A,turn='skip-turn'),'-Reason','No durable change')
check('No-change turn is skipped without repeated reminders',hook(A,PA,event='Stop',turn='skip-turn')=={})
hook(A,PA,turn='missing-turn')
reminder=hook(A,PA,event='Stop',turn='missing-turn')
again=hook(A,PA,event='Stop',turn='missing-turn')
check('Missing checkpoint gets one bounded reminder',reminder.get('decision')=='block' and 'decision' not in again)
check('stop_hook_active prevents recursion',hook(A,PA,event='Stop',turn='continuation',stop_hook_active=True)=={})
before=len(list((A[0]/'shared-memory/tickets').glob('*.json')))
invoke(A,'Hook',payload=dict(cwd=str(PA),hook_event_name='UserPromptSubmit',session_id='s',turn_id='checkpoint',prompt='[ONEDRIVE_MEMORY_CHECKPOINT] finish'))
check('Checkpoint continuation creates no new ticket',before==len(list((A[0]/'shared-memory/tickets').glob('*.json'))))
SA=invoke(A,'Status','-ProjectPath',ROOT)
SB=invoke(B,'Status','-ProjectPath',ROOT)
check('Unbound folders remain device-specific',SA['current_project']['id']!=SB['current_project']['id'])
invoke(A,'Bind','-ProjectPath',PA,'-ProjectId','other-project',ok=False)
invoke(A,'Read','-ProjectId','../escape',ok=False)
check('Project rebinding and path traversal are rejected')
secret=ROOT/'secret-example.md'; secret.write_text('# Do not store\napi_key = sk-'+'x'*30,encoding='utf-8')
hook(A,PA,turn='secret-turn')
invoke(A,'Save','-Ticket',ticket(A,turn='secret-turn'),'-NoteFile',secret,ok=False)
check('Credential-shaped content is rejected')
# Simulate an unavailable target without moving or deleting the existing shared folder.
C=install('PC-C')
cfg=C[0]/'shared-memory/config.json'; data=json.loads(cfg.read_text('utf-8'))
offline=ROOT/'temporarily-unavailable'; data['shared_root']=str(offline); cfg.write_text(json.dumps(data),encoding='utf-8')
invoke(C,'Bind','-ProjectPath',PA,'-ProjectId','sap-purchasing')
hook(C,PA)
queued=invoke(C,'Save','-Ticket',ticket(C),'-NoteFile',note)
check('Unavailable shared folder queues locally',queued['pending_delivery']==1 and not offline.exists())
offline.mkdir(); flushed=invoke(C,'Flush')
check('Queued notes deliver on retry without data loss',flushed['pending_delivery']==0 and len(list(offline.rglob('*.md')))==1)
# Simulate a crash after staging but before the receipt: the deterministic filename recovers.
receipt=json.loads(ticket(C).read_text('utf-8'))['key']
receipt_path=C[0]/'shared-memory/receipts'/f'{receipt}.json'
receipt_path.unlink()
invoke(C,'Save','-Ticket',ticket(C),'-NoteFile',note)
check('Retry after receipt loss does not duplicate a delivered note',len(list(offline.rglob('*.md')))==1)
# Corruption is deliberately confined to the scratch fixture.
original.write_bytes(original_bytes+b'partial change')
loaded=invoke(B,'Read','-ProjectPath',PB)
if isinstance(loaded,dict): loaded=[loaded]
check('Modified or incomplete records are excluded',len(loaded)==2)
repeat=command(PACKAGE/'Install.ps1','-SharedRoot',SHARED,'-CodexRoot',A[0],'-DeviceName','PC-A')
hooks=json.loads((A[0]/'hooks.json').read_text('utf-8'))
own=[h for groups in hooks['hooks'].values() for group in groups for h in group['hooks'] if 'memory.ps1' in h['command']]
check('Reinstall preserves identity and does not duplicate hooks',repeat['device_id']==A[2]['device_id'] and len(own)==3)
check('Existing user hooks and guidance are preserved','unrelated-hook' in (A[0]/'hooks.json').read_text('utf-8') and 'Existing user guidance.' in (A[0]/'AGENTS.md').read_text('utf-8'))
result=subprocess.run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(PACKAGE/'Uninstall.ps1'),'-CodexRoot',str(A[0])],capture_output=True,timeout=30)
assert result.returncode==0,result.stderr
check('Disable preserves historical notes and unrelated hooks',len(list(records.glob('*.md')))==3 and 'unrelated-hook' in (A[0]/'hooks.json').read_text('utf-8') and 'memory.ps1' not in (A[0]/'hooks.json').read_text('utf-8'))
report={'passed':len(checks),'checks':checks,'fixture':str(ROOT),'scope':'PowerShell 5.1 scripts and two isolated local installations; no real OneDrive network or second computer involved.'}
(BASE/'verification-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
