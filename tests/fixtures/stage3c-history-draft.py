"""Transactional CAD operations, separate from the preserved generation sources.

Scope: valid mechanism states operated through this API in one FreeCAD document.
Native GUI/property edits and history across file reopen are outside this contract.
"""
from state import validate_state, validate_document, transition


def current(doc):
    return {"angle_degrees": doc.getObject("Mechanism").Angle.Value,
            "bolt_m": doc.getObject("LockMechanism").BoltPosition.Value / 1000}


def apply_state(doc, angle_degrees, bolt_m, label="Stage3C mechanism state"):
    # Reject before opening a transaction: invalid requests cannot consume Redo.
    validate_state(angle_degrees, bolt_m)
    validate_document(doc)
    before = current(doc)
    if angle_degrees != before['angle_degrees'] and bolt_m != before['bolt_m']:
        raise ValueError('COMBINED_OPERATION: unlock or close in a separate step')
    if before == {"angle_degrees": angle_degrees, "bolt_m": bolt_m}:
        return current(doc)
    if not doc.UndoMode:
        doc.UndoMode = 1
    doc.openTransaction(label)
    try:
        result = transition(doc, angle_degrees, bolt_m)
        doc.commitTransaction()
        return result
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def undo(doc):
    validate_document(doc)
    doc.undo()
    doc.recompute()
    validate_document(doc)
    return current(doc)


def redo(doc):
    validate_document(doc)
    doc.redo()
    doc.recompute()
    validate_document(doc)
    return current(doc)


def reset(doc):
    """Closed and unlocked is one undoable operation; history is not cleared."""
    return apply_state(doc, 0, 0, "Stage3C reset mechanism")
