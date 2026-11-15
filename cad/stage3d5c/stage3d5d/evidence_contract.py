"""Exact archive coverage against an independently fixed expected inventory.

Saved-byte equality is separate from original completeness. Missing hidden files
are failures even if every remaining member, upload receipt and CRC are valid.
"""
from pathlib import PurePosixPath
import zipfile,hashlib

def audit_archive(path,expected):
    reasons=[];seen={}
    try:
        with zipfile.ZipFile(path) as z:
            names=[i.filename for i in z.infolist() if not i.is_dir()]
            if len(names)!=len(set(names)):reasons.append('DUPLICATE_MEMBER')
            for name in names:
                if name.startswith('/') or '..' in PurePosixPath(name).parts or '\\' in name:reasons.append('UNSAFE_MEMBER')
            if set(names)!=set(expected):
                if set(expected)-set(names):reasons.append('MISSING_MEMBER')
                if set(names)-set(expected):reasons.append('UNEXPECTED_MEMBER')
            for name in set(names)&set(expected):
                b=z.read(name);row=expected[name]
                if len(b)!=row['size'] or hashlib.sha256(b).hexdigest()!=row['sha256']:reasons.append('MEMBER_BYTES_MISMATCH')
                seen[name]={'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
            if z.testzip() is not None:reasons.append('CRC_FAILURE')
    except (zipfile.BadZipFile,RuntimeError,KeyError,ValueError,OSError) as e:reasons.append('ARCHIVE_ERROR:'+type(e).__name__)
    return {'status':'FAIL' if reasons else 'PASS','reasons':sorted(set(reasons)),
            'missing':sorted(set(expected)-set(seen)),'verified_members':seen,
            'scope':'bytes and expected inventory; not result semantics or CAD proof'}

def compare_reference(candidate,reference):
    """All observation fields compared; no selective counts-only acceptance."""
    reasons=[]
    if candidate!=reference:reasons.append('FIXED_OBSERVATION_CHANGED')
    return {'status':'FAIL' if reasons else 'PASS','reasons':reasons,'native_set_proof':'UNKNOWN'}
