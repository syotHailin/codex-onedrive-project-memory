import json
import os
from pathlib import Path
import subprocess
import uuid

base = Path(__file__).resolve().parent
root = base / ('setup-check-' + uuid.uuid4().hex[:8])
root.mkdir()
shared = root / 'Shared Library'
ps = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
script = base.parent / 'scripts/Prepare-SharedFolder.ps1'

def run():
    return subprocess.run([ps, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script), '-SharedRoot', str(shared)], capture_output=True, timeout=30)

first = run()
assert first.returncode == 0, first.stderr
assert json.loads(first.stdout)['prepared'] is True
marker = (shared/'CodexSharedMemory.Library.json').read_bytes()
second = run()
assert second.returncode == 0, second.stderr
assert (shared/'CodexSharedMemory.Library.json').read_bytes() == marker
target = shared/'setup/v1.0.0/Install.ps1'
target.write_bytes(target.read_bytes() + b'\n# Deliberate test-only change\n')
before = target.read_bytes()
third = run()
assert third.returncode != 0
assert target.read_bytes() == before
print('PASS Shared setup creates a portable library and all package files')
print('PASS Repeated preparation preserves library identity')
print('PASS Different existing setup contents are rejected without overwrite')
