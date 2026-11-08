import pathlib, tempfile, shutil, subprocess, json
root=pathlib.Path(__file__).resolve().parents[3]
evidence=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="castle-b-review-") as td:
    copy=pathlib.Path(td)/"repo"
    shutil.copytree(root,copy,ignore=shutil.ignore_patterns(".git","node_modules","dist"))
    shutil.copytree(evidence/"snapshot",copy,dirs_exist_ok=True)
    shutil.copyfile(evidence/"controls.mjs",copy/"controls.mjs")
    green=(root/"scripts/verification-register.mjs").read_bytes()
    out={}
    for label,code in [("red",(evidence/"old-verification-register.mjs.txt").read_bytes()),("green",green)]:
        (copy/"scripts/verification-register.mjs").write_bytes(code)
        p=subprocess.run(["node","controls.mjs"],cwd=copy,capture_output=True,text=True)
        if p.returncode: raise RuntimeError(p.stderr)
        out[label]=json.loads(p.stdout)
    assert all(x["accepted"] for x in out["red"]),out
    assert all(not x["accepted"] for x in out["green"]),out
    print(json.dumps(out,ensure_ascii=False,indent=2))
