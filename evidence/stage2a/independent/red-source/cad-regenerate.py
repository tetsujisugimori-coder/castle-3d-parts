#!/usr/bin/env python3
"""Stage 2-A working-copy runner; research-cad.mjs revalidates authorization."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_path(raw):
    path=Path(os.path.abspath(raw))
    if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('SYMLINK_FORBIDDEN')
    return path

def parameters(p):
    if not isinstance(p,dict) or set(p)!={'height','spacing','width','count','rails'}:raise ValueError('PARAMETERS')
    for k in ('height','spacing','width'):
        if type(p[k]) not in (int,float) or not math.isfinite(p[k]):raise ValueError('NONFINITE_'+k)
    if type(p['count']) is not int or type(p['rails']) is not int:raise ValueError('INTEGER')
    if not .1<=p['height']<=10 or not .01<=p['width']<=1 or not p['width']<p['spacing']<=10:raise ValueError('DIMENSIONS')
    if not 2<=p['count']<=30 or not 0<=p['rails']<=6:raise ValueError('COUNTS')
    if p['rails'] and p['height']/(p['rails']+1)<=p['width']*.56:raise ValueError('RAIL_OVERLAP')

def run(application,output):
    application=safe_path(application)
    output=safe_path(output)
    if not application.is_file():raise ValueError('APPLICATION_MISSING')
    protected=[ROOT/x for x in ('cad/prototype-v1','blender/prototype-v1','site','research')]
    if output==ROOT or any(output==p or p in output.parents for p in protected):raise ValueError('PROTECTED_OUTPUT')
    if output.exists():raise ValueError('OUTPUT_EXISTS')
    if not output.parent.is_dir():raise ValueError('OUTPUT_PARENT_MISSING')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    before={name:digest(ROOT/name) for name in tracked if name and (ROOT/name).is_file()}
    command=['node',str(ROOT/'scripts/research-cad.mjs'),'validate-application','--application',str(application)]
    validation=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    if validation.returncode:raise ValueError('AUTHORIZATION_REJECTED: '+validation.stderr.strip())
    auth=json.loads(validation.stdout)
    if auth.get('part_id')!='wooden-palisade-late-sengoku-v0' or auth.get('basis')!='D' or auth.get('scope')!='working_copy_only':raise ValueError('APPLICATION_SCOPE')
    parameters(auth['parameters'])
    source=safe_path(ROOT/auth['source_cad']['path'])
    if source.suffix.lower()!='.fcstd' or not source.is_file() or digest(source)!=auth['source_cad']['sha256']:raise ValueError('SOURCE_HASH')
    output.mkdir()
    manifest={'status':'RUNNING','scope':'working_copy_only','basis':'D','historical_dimensions':'NOT_ESTABLISHED','application_sha256':digest(application),'input':auth['source_cad'],'parameters':auth['parameters'],'commands':[command],'validation_stdout':validation.stdout,'validation_stderr':validation.stderr,'software_execution':'headless only; GUI NOT_TESTED'}
    try:
        shutil.copyfile(source,output/'input.FCStd')
        if digest(output/'input.FCStd')!=auth['source_cad']['sha256']:raise ValueError('COPY_HASH')
        (output/'validated-application.json').write_text(json.dumps(auth,indent=2)+'\n')
        jobs=[['/usr/bin/python3','-B',str(ROOT/'cad/stage2a/regenerate.py'),str(output)],['/usr/bin/blender','--background','--factory-startup','--python',str(ROOT/'blender/stage2a/regenerate.py'),'--',str(output)]]
        for index,cmd in enumerate(jobs):
            check=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
            manifest['commands'].append(command)
            if check.returncode or json.loads(check.stdout)!=auth:raise ValueError('AUTHORIZATION_CHANGED')
            manifest['commands'].append(cmd)
            with (output/f'command-{index+1}.log').open('w') as log:
                result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},timeout=180)
            if result.returncode:raise RuntimeError('SOFTWARE_EXIT_'+str(result.returncode))
        for name in ('freecad-audit.json','blender-audit.json','palisade.FCStd','palisade.step','mesh-transfer.json','palisade.blend','palisade.glb'):
            if not (output/name).is_file():raise RuntimeError('OUTPUT_MISSING_'+name)
        manifest['freecad']=json.loads((output/'freecad-audit.json').read_text())
        manifest['blender']=json.loads((output/'blender-audit.json').read_text())
        manifest['status']='PASS'
    except Exception as exc:
        manifest['status']='FAIL'
        manifest['error']=str(exc)
        raise
    finally:
        changed=[name for name,sha in before.items() if not (ROOT/name).is_file() or digest(ROOT/name)!=sha]
        manifest['original_tracked_files_unchanged']=not changed
        manifest['changed_tracked_files']=changed
        if changed:manifest['status']='FAIL'
        manifest['outputs']={p.name:digest(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='manifest.json'}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if changed:raise RuntimeError('ORIGINALS_CHANGED')
    return manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        result=run(args.application,args.output)
        print(json.dumps({'status':result['status'],'manifest':str(Path(args.output)/'manifest.json')}))
    except Exception as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(1)
