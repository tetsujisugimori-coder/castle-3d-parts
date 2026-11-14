"""Domain and transaction-ledger tests, NOT native FreeCAD acceptance.

The double deliberately clears Redo when opening a new native transaction, as
FreeCAD 1.0 Document::_openTransaction does. Abort cannot recover discarded Redo.
"""
import copy
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import history
from state import validate_state


class Document:
    def __init__(self):
        self.pose = (0, 0)
        self.before = None
        self.past = []
        self.future = []
        self.past_names = []
        self.future_names = []
        self.name = None
        self.UndoMode = 0
        self.transactions = 0
        self.limit = None

    @property
    def UndoCount(self):
        return len(self.past)

    @property
    def RedoCount(self):
        return len(self.future)

    @property
    def UndoNames(self):
        return self.past_names[::-1]

    @property
    def RedoNames(self):
        return self.future_names[::-1]

    @property
    def HasPendingTransaction(self):
        return self.before is not None

    def getObject(self, name):
        return NS(Angle=NS(Value=self.pose[0])) if name == 'Mechanism' else NS(BoltPosition=NS(Value=self.pose[1] * 1000))

    def recompute(self):
        pass

    def openTransaction(self, label):
        assert self.before is None
        self.before = self.pose
        self.name = label
        self.future.clear()
        self.future_names.clear()
        self.transactions += 1

    def commitTransaction(self):
        self.past.append(self.before)
        self.past_names.append(self.name)
        if self.limit is not None:
            self.past[:] = self.past[-self.limit:]
            self.past_names[:] = self.past_names[-self.limit:]
        self.before = self.name = None

    def abortTransaction(self):
        self.pose, self.before = self.before, None
        self.name = None

    def undo(self):
        if self.past:
            self.future.append(self.pose)
            self.future_names.append(self.past_names.pop())
            self.pose = self.past.pop()

    def redo(self):
        if self.future:
            self.past.append(self.pose)
            self.past_names.append(self.future_names.pop())
            self.pose = self.future.pop()


def valid(doc):
    return validate_state(*doc.pose)


def move(doc, a, b):
    validate_state(a, b)
    doc.pose = (a, b)
    return history.current(doc)


class HistoryContract(unittest.TestCase):
    def setUp(self):
        self.doc = Document()
        p = patch.multiple(history, validate_document=valid, transition=move)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(lambda: history.end_session(self.doc))

    def test_multiple_operations_undo_redo(self):
        poses = [(0, .07), (0, .14), (0, 0), (45, 0), (90, 0)]
        for pose in poses:
            history.apply_state(self.doc, *pose)
        for expected in [(45, 0), (0, 0), (0, .14), (0, .07), (0, 0)]:
            history.undo(self.doc)
            self.assertEqual(self.doc.pose, expected)
        for expected in poses:
            history.redo(self.doc)
            self.assertEqual(self.doc.pose, expected)

    def test_repeated_undo_redo(self):
        history.apply_state(self.doc, 0, .14)
        for _ in range(50):
            history.undo(self.doc)
            self.assertEqual(self.doc.pose, (0, 0))
            history.redo(self.doc)
            self.assertEqual(self.doc.pose, (0, .14))

    def test_new_operation_discards_redo(self):
        history.apply_state(self.doc, 45, 0)
        history.undo(self.doc)
        history.apply_state(self.doc, 0, .14)
        history.redo(self.doc)
        self.assertEqual(self.doc.pose, (0, .14))
        self.assertEqual(self.doc.RedoCount, 0)

    def test_rejection_preserves_both_stacks(self):
        history.apply_state(self.doc, 45, 0)
        history.undo(self.doc)
        before = copy.deepcopy(self.doc.__dict__)
        for pose in [(45, .001), (-1, 0), (91, 0), (0, float('nan')), (True, 0)]:
            with self.assertRaises(ValueError):
                history.apply_state(self.doc, *pose)
            self.assertEqual(self.doc.__dict__, before)
        history.redo(self.doc)
        self.assertEqual(self.doc.pose, (45, 0))

    def test_noop_preserves_redo(self):
        history.apply_state(self.doc, 45, 0)
        history.undo(self.doc)
        before = copy.deepcopy(self.doc.__dict__)
        history.apply_state(self.doc, 0, 0)
        self.assertEqual(self.doc.__dict__, before)
        history.redo(self.doc)
        self.assertEqual(self.doc.pose, (45, 0))

    def test_no_implicit_unlock_or_close(self):
        for first, forbidden in [((0, .14), (45, 0)), ((45, 0), (0, .14))]:
            doc = Document()
            history.apply_state(doc, *first)
            before = copy.deepcopy(doc.__dict__)
            with self.assertRaisesRegex(ValueError, 'COMBINED_OPERATION'):
                history.apply_state(doc, *forbidden)
            self.assertEqual(doc.__dict__, before)
            history.end_session(doc)

    def test_reset_is_undoable(self):
        history.apply_state(self.doc, 0, .14)
        history.reset(self.doc)
        history.undo(self.doc)
        self.assertEqual(self.doc.pose, (0, .14))
        history.redo(self.doc)
        self.assertEqual(self.doc.pose, (0, 0))

    def test_unowned_invalid_native_targets_rejected_before_mutation(self):
        for direction in ['undo', 'redo']:
            doc = Document()
            values = doc.past if direction == 'undo' else doc.future
            names = doc.past_names if direction == 'undo' else doc.future_names
            values.append((45, .14))
            names.append('external invalid state')
            before = copy.deepcopy(doc.__dict__)
            with self.assertRaisesRegex(ValueError, 'HISTORY_UNOWNED'):
                getattr(history, direction)(doc)
            self.assertEqual(doc.__dict__, before)

    def test_external_native_history_rejected(self):
        history.begin_session(self.doc)
        self.doc.past.append((45, .14))
        self.doc.past_names.append('external invalid state')
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'HISTORY_EXTERNAL_CHANGE'):
            history.undo(self.doc)
        self.assertEqual(self.doc.__dict__, before)

    def test_illegal_ledger_target_rejected_before_native_undo(self):
        history.apply_state(self.doc, 45, 0)
        history._sessions[id(self.doc)].past[-1]['before'] = {'angle_degrees': 45, 'bolt_m': .14}
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'INTERLOCK'):
            history.undo(self.doc)
        self.assertEqual(self.doc.__dict__, before)

    def test_unexpected_native_target_is_recovered(self):
        history.apply_state(self.doc, 45, 0)
        # Counts/names alone cannot predict a malicious native implementation.
        self.doc.past[-1] = (45, .14)
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'INTERLOCK'):
            history.undo(self.doc)
        self.assertEqual(self.doc.__dict__, before)
        self.assertEqual(history.current(self.doc), {'angle_degrees': 45, 'bolt_m': 0})

    def test_unexpected_native_redo_target_is_recovered(self):
        history.apply_state(self.doc, 45, 0)
        history.undo(self.doc)
        self.doc.future[-1] = (45, .14)
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'INTERLOCK'):
            history.redo(self.doc)
        self.assertEqual(self.doc.__dict__, before)

    def test_same_count_native_name_substitution_is_not_accepted(self):
        for direction in ['undo', 'redo']:
            doc = Document()
            history.apply_state(doc, 45, 0)
            if direction == 'redo':
                history.undo(doc)
            before_pose = doc.pose
            native_travel = getattr(doc, direction)
            def substituted_name():
                native_travel()
                names = doc.future_names if direction == 'undo' else doc.past_names
                names[-1] = 'unowned replacement with unchanged counts'
            with patch.object(doc, direction, substituted_name):
                with self.assertRaisesRegex(RuntimeError, 'HISTORY_RECOVERY_FAILED'):
                    getattr(history, direction)(doc)
            # Native transaction names have no public setter. A corrupt native
            # history cannot be silently adopted; pose restored, session blocked.
            self.assertEqual(doc.pose, before_pose)
            with self.assertRaisesRegex(ValueError, 'HISTORY_SESSION_UNAVAILABLE'):
                history.undo(doc)
            history.end_session(doc)

    def test_pending_transaction_is_not_adopted(self):
        self.doc.openTransaction('external pending')
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'HISTORY_PENDING_TRANSACTION'):
            history.undo(self.doc)
        self.assertEqual(self.doc.__dict__, before)

    def test_native_stack_limit_trims_only_oldest_owned_history(self):
        self.doc.limit = 2
        for angle in [10, 20, 30, 40]:
            history.apply_state(self.doc, angle, 0)
        self.assertEqual(self.doc.UndoCount, 2)
        history.undo(self.doc)
        self.assertEqual(self.doc.pose, (30, 0))
        history.undo(self.doc)
        self.assertEqual(self.doc.pose, (20, 0))
        history.undo(self.doc)
        self.assertEqual(self.doc.pose, (20, 0))

    def test_direct_invalid_property_state_rejected(self):
        history.begin_session(self.doc)
        self.doc.pose = (45, .14)
        before = copy.deepcopy(self.doc.__dict__)
        with self.assertRaisesRegex(ValueError, 'INTERLOCK'):
            history.undo(self.doc)
        self.assertEqual(self.doc.__dict__, before)

    def test_save_reopen_has_state_but_no_session_history(self):
        history.apply_state(self.doc, 0, .14)
        saved_pose = self.doc.pose
        reopened = Document()
        reopened.pose = saved_pose  # Native document persists geometry/state only.
        history.undo(reopened)
        self.assertEqual(reopened.pose, saved_pose)
        self.assertEqual((reopened.UndoCount, reopened.RedoCount), (0, 0))
        history.end_session(reopened)

    def test_transaction_failure_aborts_without_existing_redo(self):
        def broken(doc, a, b):
            doc.pose = (a, b)
            raise RuntimeError('injected failure')
        with patch.object(history, 'transition', broken), self.assertRaisesRegex(RuntimeError, 'injected failure'):
            history.apply_state(self.doc, 90, 0)
        self.assertEqual(self.doc.pose, (0, 0))
        self.assertEqual((self.doc.UndoCount, self.doc.RedoCount), (0, 0))
        self.assertFalse(self.doc.HasPendingTransaction)

    def test_native_runtime_failure_does_not_claim_redo_recovery(self):
        history.apply_state(self.doc, 45, 0)
        history.undo(self.doc)
        def broken(doc, a, b):
            doc.pose = (a, b)
            raise RuntimeError('native runtime failure')
        with patch.object(history, 'transition', broken), self.assertRaisesRegex(RuntimeError, 'HISTORY_RECOVERY_FAILED'):
            history.apply_state(self.doc, 90, 0)
        self.assertEqual(self.doc.pose, (0, 0))
        with self.assertRaisesRegex(ValueError, 'HISTORY_SESSION_UNAVAILABLE'):
            history.redo(self.doc)


if __name__ == '__main__':
    unittest.main()
