import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

base=Path(__file__).resolve().parent
root=base/('launcher-check-'+uuid.uuid4().hex[:8])
shared=root/'SharedLibrary'
package=shared/'setup/v1.0.0'
package.parent.mkdir(parents=True)
shutil.copytree(base.parent/'package',package)
(shared/'CodexSharedMemory.Library.json').write_text(json.dumps({'library_type':'codex-project-memory','schema_version':1}),encoding='utf-8')
env=os.environ.copy();env['CODEX_HOME']=str(root/'local-codex')
ps=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe')
def run(file,*args):
    p=subprocess.run([ps,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(file),*map(str,args)],env=env,capture_output=True,timeout=30)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    return p.stdout
result=json.loads(run(package/'Install-This-PC.ps1'))
assert result['shared_root']==str(shared)
project=root/'project';project.mkdir()
run(package/'Connect-Project.ps1','-ProjectPath',project,'-ProjectId','launcher-test')
config=json.loads((root/'local-codex/shared-memory/config.json').read_text('utf-8'))
assert config['bindings'][0]['project_id']=='launcher-test'
hooks=json.loads((root/'local-codex/hooks.json').read_text('utf-8'))
command=hooks['hooks']['UserPromptSubmit'][0]['hooks'][0]['command']
payload={'session_id':'launcher-test','turn_id':'1','cwd':str(project),'hook_event_name':'UserPromptSubmit','prompt':'Check installed command'}
p=subprocess.run(command,input=json.dumps(payload).encode(),env=env,capture_output=True,timeout=30)
assert p.returncode==0,p.stderr
context=json.loads(p.stdout.decode('utf-8-sig'))
assert context['hookSpecificOutput']['hookEventName']=='UserPromptSubmit',context
print('PASS OneDrive launcher resolves the shared root independently of drive letter')
print('PASS Project binding launcher uses the local Codex configuration')
print('PASS Exact installed Windows hook command accepts stdin and emits valid JSON')
