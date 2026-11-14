"""Actual FreeCAD transactions/BRep/reopen test; never run as portable evidence.

Run from a FreeCAD-enabled Python runtime with SOURCE.FCStd and a new output
directory as arguments. Copies only the 70KB source FCStd; never overwrites it.
Then launch a second process with first-output/history-result.FCStd, a second new
output directory and --reopen-only to prove cross-process state/history behavior.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import FreeCAD as A
from state import load_document, validate_document
from history import apply_state, undo, redo, reset, current, begin_session, end_session


parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--reopen-only', action='store_true')
args = parser.parse_args()
source = args.source.resolve()
work = args.output.resolve()
if work.exists():
    raise SystemExit('Refusing existing output directory')
work.mkdir(parents=True)
tempfile.tempdir = str(work)  # restore() transient paths stay in this test area.
shutil.copyfile(source, work / 'input.FCStd')
doc = load_document(work / 'input.FCStd', 'Stage3CHistoryNative')
for obj in doc.Objects:
    if 'KeepUpdated' in obj.PropertiesList:
        obj.KeepUpdated = False
doc.recompute()
if args.reopen_only:
    validate_document(doc)
    assert current(doc) == {'angle_degrees': 0, 'bolt_m': .14}
    assert doc.UndoCount == 0 and doc.RedoCount == 0
    expected = json.loads((source.parent / 'history-native-result.json').read_text())
    reference = next(row for row in expected['checks'] if row['state'] == current(doc))
    for name, key in [('GATE_Door', 'door_bounds_mm'), ('GATE_Bolt', 'bolt_bounds_mm')]:
        box = doc.getObject(name).Shape.BoundBox
        actual = [getattr(box, k) for k in ['XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax']]
        assert all(abs(a-b) < 1e-6 for a, b in zip(actual, reference[key]))
    begin_session(doc)
    before = current(doc)
    undo(doc)
    assert current(doc) == before and doc.UndoCount == 0 and doc.RedoCount == 0
    result = {'status': 'PASS', 'FreeCAD': A.Version(),
              'separate_process_state_geometry_match': True,
              'old_session_history_not_restored': True,
              'scope': 'actual separate-process FreeCAD readback; not manual GUI'}
    (work / 'separate-process-result.json').write_text(json.dumps(result, indent=2))
    A.closeDocument(doc.Name)
    print(json.dumps(result, indent=2))
    sys.exit(0)
# Explicit test setup only: do not imply that begin_session discards user history.
doc.UndoMode = 1
doc.clearUndos()
begin_session(doc)
rows = []


def snapshot():
    def bounds(name):
        box = doc.getObject(name).Shape.BoundBox
        return [getattr(box, k) for k in ['XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax']]
    return {'state': current(doc), 'undo': doc.UndoCount, 'redo': doc.RedoCount,
            'undo_names': list(doc.UndoNames), 'redo_names': list(doc.RedoNames),
            'door_bounds_mm': bounds('GATE_Door'), 'bolt_bounds_mm': bounds('GATE_Bolt')}


def expect(angle, bolt):
    validate_document(doc)
    assert current(doc) == {'angle_degrees': angle, 'bolt_m': bolt}, current(doc)
    row = snapshot()
    for old in rows:
        if old['state'] == row['state']:
            for key in ['door_bounds_mm', 'bolt_bounds_mm']:
                assert all(abs(x-y) < 1e-6 for x, y in zip(old[key], row[key])), key
    rows.append(row)


expect(0, 0)
poses = [(0, .07), (0, .14), (0, 0), (45, 0), (90, 0)]
for pose in poses:
    apply_state(doc, *pose)
    expect(*pose)
for pose in [(45, 0), (0, 0), (0, .14), (0, .07), (0, 0)]:
    undo(doc)
    expect(*pose)
for pose in poses:
    redo(doc)
    expect(*pose)
undo(doc)
expect(45, 0)
before = snapshot()
for pose in [(45, .001), (-1, 0), (91, 0), (0, float('nan')), (True, 0)]:
    try:
        apply_state(doc, *pose)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid operation accepted')
    assert snapshot() == before
redo(doc)
expect(90, 0)
for _ in range(25):
    undo(doc)
    expect(45, 0)
    redo(doc)
    expect(90, 0)
undo(doc)
apply_state(doc, 30, 0)
redo(doc)
expect(30, 0)
reset(doc)
expect(0, 0)
undo(doc)
expect(30, 0)
redo(doc)
expect(0, 0)
apply_state(doc, 0, .14)
reset(doc)
undo(doc)
expect(0, .14)

# A saved document retains legal geometry/state; this API's ledger is not a
# persistent FreeCAD property and no Undo across process reopen is promised.
saved = snapshot()
doc.saveAs(str(work / 'history-result.FCStd'))
name = doc.Name
end_session(doc)
A.closeDocument(name)
doc = load_document(work / 'history-result.FCStd', 'Stage3CHistoryReopened')
assert doc.UndoCount == 0 and doc.RedoCount == 0, 'Reopen must not adopt old native history'
begin_session(doc)
expect(0, .14)
assert snapshot()['bolt_bounds_mm'] == saved['bolt_bounds_mm']
undo(doc)
expect(0, .14)

# A direct property edit is not silently accepted into the API-owned ledger.
doc.getObject('Mechanism').Angle = 45
doc.recompute()
bad = snapshot()
try:
    undo(doc)
except ValueError as error:
    assert str(error) == 'INTERLOCK'
else:
    raise AssertionError('Direct invalid property edit accepted')
assert snapshot() == bad
doc.saveAs(str(work / 'invalid-direct-edit.FCStd'))
end_session(doc)
A.closeDocument(doc.Name)
doc = load_document(work / 'invalid-direct-edit.FCStd', 'Stage3CHistoryInvalidReopened')
try:
    validate_document(doc)
except ValueError as error:
    assert str(error) == 'INTERLOCK'
else:
    raise AssertionError('Persisted illegal direct edit accepted')
A.closeDocument(doc.Name)

result = {'status': 'PASS', 'FreeCAD': A.Version(), 'checks': rows,
          'state_persisted_history_not_persisted': True,
          'direct_invalid_saved_reloaded_rejected': True,
          'scope': 'actual FreeCAD transactions and BRep bounds; not manual GUI'}
(work / 'history-native-result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
