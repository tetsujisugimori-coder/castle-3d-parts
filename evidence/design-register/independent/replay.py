import pathlib,tempfile,subprocess,shutil,json,os
root=pathlib.Path(__file__).resolve().parents[3]; evidence=root/'evidence/design-register/independent'
def run(cmd,cwd,env=None):
 p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True);return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def copy():
 t=pathlib.Path(tempfile.mkdtemp(prefix='castle-stage4-review-'))/'repo';subprocess.run(['git','clone','--shared',str(root),str(t)],check=True,capture_output=True)
 shutil.copytree(root,t,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
 return t
old=copy();shutil.copyfile(evidence/'old-design-register.mjs.txt',old/'scripts/design-register.mjs');shutil.copyfile(evidence/'old-decision.schema.json',old/'design/schema/decision.schema.json');shutil.copyfile(evidence/'old-baseline.json',old/'design/baseline.json')
for p in (evidence/'old-decisions').glob('*.json'):shutil.copyfile(p,old/'design/decisions'/p.name)
red=run(['node','evidence/design-register/independent/controls.mjs'],old)
green=run(['node','evidence/design-register/independent/controls.mjs'],root)
t=copy();p=t/'design/decisions/DEC-0001-r2.json';d=json.loads((t/'design/decisions/DEC-0001-r1.json').read_text());d.update(revision=2,previous='DEC-0001-r1.json',reason='独立試験用の保留継続',created_at='2026-11-09T00:00:00Z');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['git','add','.'],cwd=t,check=True);subprocess.run(['git','-c','user.name=Independent Review','-c','user.email=review@example.invalid','commit','-m','Synthetic prior history for isolated negative control'],cwd=t,check=True,capture_output=True)
base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=t,text=True).strip();p.unlink();env=dict(os.environ,PR_BASE_SHA=base);removed=run(['node','--input-type=module','-e',"import{preserve}from'./scripts/design-register.mjs';preserve();"],t,env)
result={'red':red,'green':green,'later_revision_deletion':removed};(evidence/'replay-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert red['exit']==1 and green['exit']==0 and removed['exit']==1 and 'PR_HISTORY_LOST' in removed['stderr']
