"""Read-only audit of actual deployed Pages bytes, with normal HTTPS validation."""
import urllib.request,urllib.error, pathlib, json, hashlib, datetime, concurrent.futures, sys
base='https://tetsujisugimori-coder.github.io/castle-3d-parts/'
expected=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
head=sys.argv[3];tree=sys.argv[4]
paths=sorted(p.relative_to(expected).as_posix() for p in expected.rglob('*') if p.is_file() and p.name!='.nojekyll')
def one(path):
 url=base+('' if path=='index.html' else path)
 row={'path':path,'url':url,'expected_sha256':hashlib.sha256((expected/path).read_bytes()).hexdigest()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=45) as r:
   raw=r.read();row.update(status=r.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),last_modified=r.headers.get('last-modified'))
   if path=='deployment-manifest.json':
    doc=json.loads(raw);(out/path).write_bytes(raw);row.update(source_commit=doc['source_commit'],source_tree=doc['source_tree']);row['match']=doc['source_commit']==head and doc['source_tree']==tree
    exp=json.loads((expected/path).read_bytes());row['asset_manifest_matches']=doc['assets']==exp['assets'];row['match']=row['match'] and row['asset_manifest_matches']
   else:row['match']=row['sha256']==row['expected_sha256']
 except Exception as e:row.update(error=str(e),match=False)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(one,paths))
doc={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual production HTTPS responses, no mocking and no TLS bypass','expected_commit':head,'expected_tree':tree,'rows':rows,'all_match':all(r['match'] for r in rows),'physical_iphone':'NOT_TESTED'}
(out/'results.json').write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps({'count':len(rows),'matched':sum(r['match'] for r in rows),'failed':[r for r in rows if not r['match']]}));sys.exit(0 if doc['all_match'] else 1)
