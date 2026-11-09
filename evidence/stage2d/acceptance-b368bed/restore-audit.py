import json,urllib.request,urllib.error,hashlib,datetime,pathlib
p=pathlib.Path('/tmp/stage2d-acceptance'); before=json.load(open(p/'production-before.json'));rows=[]
for original in before['rows']:
 url=original['url'];request=urllib.request.Request(url,headers={'Cache-Control':'no-cache'})
 try:r=urllib.request.urlopen(request,timeout=30)
 except urllib.error.HTTPError as e:r=e
 with r:
  raw=r.read();status=r.status;sha=hashlib.sha256(raw).hexdigest()
 rows.append({'url':url,'status':status,'sha256':sha,'expected_status':original['status'],'expected_sha256':original['sha256'],'status_match':status==original['status'],'bytes_match':sha==original['sha256'],'linked_viewer_entry_present':b'linked-viewer-entry' in raw})
d={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'restoration_run':42607054459,'main_sha':'dec85b596f6b82bfd69129e4b1edbc75d182318c','all_match':all(x['status_match'] and x['bytes_match'] for x in rows),'rows':rows,'scope':'Actual HTTPS responses after original main redeployment; environment protection is separately verified'}
(p/'production-restoration.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
