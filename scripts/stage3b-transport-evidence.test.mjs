import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { auditEvidence, outcome } from './stage3b-transport-evidence.mjs';

const PNG = Buffer.from('89504e470d0a1a0a0000000d49484452', 'hex');
const ZIP = Buffer.concat([Buffer.from('504b0304', 'hex'), Buffer.alloc(40), Buffer.from('504b0506', 'hex'), Buffer.alloc(18)]);
const makeRows = () => Array.from({ length: 6 }, (_, i) => ({
  tag: 'case-' + i, synthetic: i === 5,
  status: i === 5 ? 'EXPECTED_SYNTHETIC_FAIL' : 'PASS',
}));
function fixture() {
  const directory = mkdtempSync(join(tmpdir(), 'stage3b-evidence-'));
  const rows = makeRows();
  for (const row of rows) {
    writeFileSync(join(directory, row.tag + '.zip'), ZIP);
    writeFileSync(join(directory, row.tag + '.png'), PNG);
  }
  writeFileSync(join(directory, 'identity.json'), '{}');
  writeFileSync(join(directory, 'results.json'), JSON.stringify(rows));
  writeFileSync(join(directory, 'transport.jsonl'), '{"type":"case-start"}\n');
  return { directory, rows, close: () => rmSync(directory, { recursive: true, force: true }) };
}
// Actual old aggregation checked only case counts and ignored traceError/screenshotError.
function oldExitCode(rows) {
  const normalPass = rows.filter(r => !r.synthetic && r.status === 'PASS').length;
  const syntheticPass = rows.filter(r => r.synthetic && r.status === 'EXPECTED_SYNTHETIC_FAIL').length;
  return normalPass === 5 && syntheticPass === 1 ? 0 : 1;
}

test('complete 5 normal and 1 synthetic case => PASS', () => {
  const f = fixture();
  try {
    const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
    assert.equal(evidence.status, 'COMPLETE');
    assert.deepEqual(outcome({ transportSuccess: true, evidenceStatus: evidence.status }), { status: 'PASS', exitCode: 0 });
  } finally { f.close(); }
});

test('P2-DIAG-01 old RED: all six trace saves fail but old aggregation returns 0; new GREEN: INCOMPLETE/2', () => {
  const f = fixture();
  try {
    for (const row of f.rows) row.traceError = 'synthetic write failure';
    assert.equal(oldExitCode(f.rows), 0);
    const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
    assert.equal(evidence.status, 'INCOMPLETE');
    assert.equal(evidence.issues.filter(x => x.includes('traceError=')).length, 6);
    assert.equal(outcome({ transportSuccess: true, evidenceStatus: evidence.status }).exitCode, 2);
    assert.equal(f.rows.filter(x => x.status === 'PASS').length, 5);
  } finally { f.close(); }
});

for (const [name, target] of [
  ['missing trace', 'case-0.zip'],
  ['missing screenshot', 'case-0.png'],
  ['missing transport log', 'transport.jsonl'],
]) {
  test('P2-DIAG-01 rejects ' + name, () => {
    const f = fixture();
    try {
      unlinkSync(join(f.directory, target));
      assert.equal(oldExitCode(f.rows), 0);
      const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
      assert.equal(evidence.status, 'INCOMPLETE');
      assert.equal(outcome({ transportSuccess: true, evidenceStatus: evidence.status }).exitCode, 2);
    } finally { f.close(); }
  });
}

test('P2-DIAG-01 rejects empty/corrupt trace and PNG', () => {
  const f = fixture();
  try {
    writeFileSync(join(f.directory, 'case-0.zip'), Buffer.alloc(0));
    writeFileSync(join(f.directory, 'case-1.zip'), Buffer.from('not a zip'));
    writeFileSync(join(f.directory, 'case-0.png'), Buffer.from('not a png'));
    const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
    assert.equal(evidence.status, 'INCOMPLETE');
    assert.ok(evidence.issues.length >= 3);
  } finally { f.close(); }
});

test('P2-DIAG-01 rejects screenshot write exception independently', () => {
  const f = fixture();
  try {
    f.rows[1].screenshotError = 'synthetic disk denial';
    const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
    assert.equal(evidence.status, 'INCOMPLETE');
    assert.equal(outcome({ transportSuccess: true, evidenceStatus: evidence.status }).exitCode, 2);
  } finally { f.close(); }
});

test('case count or duplicate tag cannot be accepted as complete', () => {
  const f = fixture();
  try {
    assert.equal(auditEvidence({ directory: f.directory, rows: f.rows.slice(1), expectedCount: 6 }).status, 'INCOMPLETE');
    const duplicate = makeRows();
    duplicate[1].tag = duplicate[0].tag;
    assert.equal(auditEvidence({ directory: f.directory, rows: duplicate, expectedCount: 6 }).status, 'INCOMPLETE');
  } finally { f.close(); }
});

test('transport FAIL remains distinct from complete evidence', () => {
  const f = fixture();
  try {
    const evidence = auditEvidence({ directory: f.directory, rows: f.rows, expectedCount: 6 });
    assert.equal(evidence.status, 'COMPLETE');
    assert.deepEqual(outcome({ transportSuccess: false, evidenceStatus: evidence.status }), { status: 'FAIL', exitCode: 1 });
  } finally { f.close(); }
});
