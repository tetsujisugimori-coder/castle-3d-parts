"""Native-proof readiness, not a certificate issuer for OCCT real sets.

Input status labels, hashes, flags and sampled discrepancies cannot discharge a
set-theoretic or real-error obligation. The supported native proof calculus is
currently empty; this is reported, never silently replaced by sampled checking.
"""
from fractions import Fraction
import hashlib,json
ERRORS=('geometry','extraction','kernel_representation','coordinate_transform','unit','arithmetic_rounding','state_generation','continuous_displacement')
REQUIRED=('material_outer','void_inner','all_state_placement','all_state_motion')

def rational(x):
    if isinstance(x,bool) or isinstance(x,float):raise ValueError('EXACT_RATIONAL_REQUIRED')
    if not isinstance(x,(str,int)):raise ValueError('EXACT_RATIONAL_REQUIRED')
    return Fraction(x)

def canonical_hash(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def evidence_kind(record):
    """Classify only; actual theorem verification is NOT implemented."""
    kind=record.get('kind')
    if kind in ('occt_flag','sample_maximum','topology_observation','represented_identity','static_pose_comparison'):
        return {'status':'UNKNOWN','reason':'NOT_A_NATIVE_REAL_SET_OR_BOUND_CERTIFICATE','kind':kind}
    return {'status':'UNKNOWN','reason':'UNSUPPORTED_NATIVE_PROOF_METHOD','kind':kind}

def assess(propositions,errors,claimed_status=None):
    if set(propositions)!=set(REQUIRED) or set(errors)!=set(ERRORS):
        return {'input_status':'FAIL','reason':'OBLIGATION_INVENTORY','representative':'NOT_TESTED'}
    terms={}; malformed=[]
    for k,r in errors.items():
        upper=r.get('upper_m')
        if upper is not None:
            try:
                if rational(upper)<0:malformed.append(k+':NEGATIVE_BOUND')
            except (ValueError,ZeroDivisionError):malformed.append(k+':INVALID_BOUND')
        terms[k]={'upper_m':None,'status':'UNKNOWN','claim':r,'classification':evidence_kind(r)}
    if malformed:return {'input_status':'FAIL','reasons':malformed,'representative':'NOT_TESTED'}
    ps={k:{'status':'UNKNOWN','claim':v,'classification':evidence_kind(v)} for k,v in propositions.items()}
    return {'input_status':'PASS','propositions':ps,'errors':terms,'native_bound_sum_m':None,
        'representative':'NOT_TESTED','actual_collision':'UNKNOWN','reason':'NATIVE_PROOF_CALCULUS_NOT_ESTABLISHED',
        'claimed_status_not_authority':claimed_status,'actual_intervals_evaluated':0,'expand_to_128':False}

def conditional_clearance(model_lower_m,reported_terms):
    """Arithmetic-only countercheck, never native-bound provenance verification."""
    if set(reported_terms)!=set(ERRORS):raise ValueError('ERROR_INVENTORY')
    if any(v is None for v in reported_terms.values()):return {'status':'UNKNOWN','lower_m':None}
    es=[rational(v) for v in reported_terms.values()]
    if any(v<0 for v in es):raise ValueError('NEGATIVE_BOUND')
    lower=rational(model_lower_m)-sum(es,Fraction(0))
    return {'status':'PASS' if lower>0 else 'UNKNOWN','lower_m':str(lower),'scope':'conditional exact arithmetic; supplied bounds not certified','native_safety':'NOT_TESTED'}

def sampling_record(maxdev,nb_control=23):
    """CheckSameParameter maxdev is a sampled maximum, not a continuous upper."""
    if isinstance(nb_control,bool) or not isinstance(nb_control,int) or nb_control<2:raise ValueError('CONTROL_COUNT')
    if rational(maxdev)<0:raise ValueError('NEGATIVE_DEVIATION')
    return {'sample_maxdev':str(rational(maxdev)),'points':nb_control,'continuous_upper':None,'native_proof':'UNKNOWN'}
