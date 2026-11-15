"""Read original ZIP without extraction; require every execution-captured source."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def audit(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError('ZIP_DUPLICATE_OR_CRC')
        records=[n for n in names if n.endswith('/execution.json')]
        if not records:raise ValueError('NO_EXECUTION_RECORDS')
        count=0
        for n in records:
            record=json.loads(z.read(n));prefix=n.rsplit('/',1)[0]+'/source/'
            sources=record.get('sources',{})
            if not sources:raise ValueError('EMPTY_SOURCE_MANIFEST')
            expected={prefix+p for p in sources}
            actual={p for p in names if p.startswith(prefix) and not p.endswith('/')}
            if expected!=actual:raise ValueError('SOURCE_SET_MISMATCH:'+str(sorted(expected-actual)))
            for p,m in sources.items():
                raw=z.read(prefix+p)
                if len(raw)!=m['bytes'] or hashlib.sha256(raw).hexdigest()!=m['sha256']:
                    raise ValueError('SOURCE_BYTES_MISMATCH:'+p)
                blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                if blob!=m['git_blob_sha']:raise ValueError('GIT_BLOB_MISMATCH:'+p)
                count+=1
        return {'execution_records':len(records),'source_instances':count,'CRC_entries':len(names),
                'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'status':'PASS'}

if __name__=='__main__':print(json.dumps(audit(sys.argv[1]),indent=2))
