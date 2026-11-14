"""Session-owned FreeCAD transactions; history is deliberately not serialized.

Only this API may edit the document while a session is active. Start with a valid
document and empty native Undo/Redo stacks (the caller explicitly clears any
unrelated history). Reopening a saved document starts a new, empty session.
FreeCAD 1.0 DocumentPy supplies UndoCount, RedoCount, UndoNames, RedoNames and
HasPendingTransaction. A test double cannot establish native acceptance.
"""
from dataclasses import dataclass, field
import uuid
from state import validate_state, validate_document, transition


@dataclass
class _Session:
    document: object
    pose: dict
    signature: tuple
    token: str = field(default_factory=lambda: uuid.uuid4().hex)
    past: list = field(default_factory=list)
    future: list = field(default_factory=list)
    serial: int = 0
    poisoned: bool = False


_sessions = {}


def current(doc):
    return {"angle_degrees": doc.getObject("Mechanism").Angle.Value,
            "bolt_m": doc.getObject("LockMechanism").BoltPosition.Value / 1000}


def _signature(doc):
    if doc.HasPendingTransaction:
        raise ValueError("HISTORY_PENDING_TRANSACTION")
    result = (doc.UndoCount, doc.RedoCount,
              tuple(doc.UndoNames), tuple(doc.RedoNames))
    if result[0] != len(result[2]) or result[1] != len(result[3]):
        raise ValueError("HISTORY_NATIVE_SIGNATURE")
    return result


def begin_session(doc):
    """Adopt a valid document with empty native history; never clears history."""
    validate_document(doc)
    signature = _signature(doc)
    if signature[0] or signature[1]:
        raise ValueError("HISTORY_UNOWNED: explicitly clear unrelated native history")
    doc.UndoMode = 1
    session = _Session(doc, current(doc), _signature(doc))
    _sessions[id(doc)] = session
    return current(doc)


def end_session(doc):
    """Forget the in-memory ledger; leaves the document and native stacks intact."""
    _sessions.pop(id(doc), None)


def _session(doc):
    validate_document(doc)
    session = _sessions.get(id(doc))
    if session is None:
        begin_session(doc)
        session = _sessions[id(doc)]
    if session.document is not doc or session.poisoned:
        raise ValueError("HISTORY_SESSION_UNAVAILABLE")
    if current(doc) != session.pose or _signature(doc) != session.signature:
        raise ValueError("HISTORY_EXTERNAL_CHANGE")
    return session


def _verify_restored(doc, session, pose, signature):
    validate_document(doc)
    if current(doc) != pose or _signature(doc) != signature:
        session.poisoned = True
        raise RuntimeError("HISTORY_RECOVERY_FAILED: native history not restored")


def apply_state(doc, angle_degrees, bolt_m, label="mechanism state"):
    # Validate *all* domain rejections before openTransaction, which clears native
    # Redo in FreeCAD 1.0. abortTransaction cannot restore a discarded Redo stack.
    validate_state(angle_degrees, bolt_m)
    session = _session(doc)
    before = dict(session.pose)
    requested = {"angle_degrees": angle_degrees, "bolt_m": bolt_m}
    if angle_degrees != before["angle_degrees"] and bolt_m != before["bolt_m"]:
        raise ValueError("COMBINED_OPERATION: unlock or close in a separate step")
    if requested == before:
        return current(doc)
    signature = session.signature
    name = "Stage3C:" + session.token + ":" + str(session.serial + 1) + ":" + label
    doc.openTransaction(name)
    try:
        result = transition(doc, angle_degrees, bolt_m)
        validate_document(doc)
        if current(doc) != requested:
            raise ValueError("HISTORY_NATIVE_STATE_MISMATCH")
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        # A native runtime failure after opening a branching transaction may have
        # destroyed Redo. Do not label rollback as successful history recovery.
        try:
            _verify_restored(doc, session, before, signature)
        except Exception:
            session.poisoned = True
            raise
        raise
    native = _signature(doc)
    if (not 1 <= native[0] <= signature[0] + 1 or native[1] != 0
            or native[2] != (name,) + signature[2][:native[0] - 1]):
        session.poisoned = True
        raise RuntimeError("HISTORY_NATIVE_COMMIT_MISMATCH")
    session.past.append({"before": before, "after": requested})
    # Native FreeCAD may evict its oldest transactions at its configured limit.
    # Trim the matching oldest ledger entries instead of inventing extra Undo.
    session.past[:] = session.past[-native[0]:]
    session.future.clear()
    session.pose = requested
    session.signature = native
    session.serial += 1
    return result


def _travel(doc, direction):
    session = _session(doc)
    source = session.past if direction == "undo" else session.future
    destination = session.future if direction == "undo" else session.past
    if not source:
        return current(doc)
    record = source[-1]
    target = record["before"] if direction == "undo" else record["after"]
    # Never execute a transaction that our ledger says leads to an illegal state.
    validate_state(target["angle_degrees"], target["bolt_m"])
    before = dict(session.pose)
    signature = session.signature
    # FreeCAD getAvailableUndoNames/getAvailableRedoNames enumerate rbegin first:
    # the top transaction name must move to the other stack, not merely change
    # the two counts. A same-count native history substitution must fail closed.
    expected = ((signature[0] - 1, signature[1] + 1,
                 signature[2][1:], signature[2][:1] + signature[3])
                if direction == "undo" else
                (signature[0] + 1, signature[1] - 1,
                 signature[3][:1] + signature[2], signature[3][1:]))
    try:
        getattr(doc, direction)()
        doc.recompute()
        validate_document(doc)
        native = _signature(doc)
        if current(doc) != target or native != expected:
            raise ValueError("HISTORY_NATIVE_RESTORE_MISMATCH")
    except Exception:
        # An unexpected native target is undone immediately, before changing the
        # trusted ledger. A failed recovery poisons this session and blocks reuse.
        try:
            if current(doc) != before or _signature(doc) != signature:
                getattr(doc, "redo" if direction == "undo" else "undo")()
                doc.recompute()
            _verify_restored(doc, session, before, signature)
        except Exception:
            session.poisoned = True
            raise
        raise
    source.pop()
    destination.append(record)
    session.pose = dict(target)
    session.signature = native
    return current(doc)


def undo(doc):
    return _travel(doc, "undo")


def redo(doc):
    return _travel(doc, "redo")


def reset(doc):
    """Closed/unlocked is one undoable operation, never a history clear."""
    return apply_state(doc, 0, 0, "reset mechanism")
