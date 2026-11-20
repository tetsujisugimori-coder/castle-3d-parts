// Evidence completeness is distinct from transport/app behavior.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const PNG = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const ZIP_LOCAL = Buffer.from([80, 75, 3, 4]);
const ZIP_END = Buffer.from([80, 75, 5, 6]);

function inspectFile(path, kind) {
  let bytes;
  try { bytes = readFileSync(path); }
  catch (error) { return 'missing/unreadable (' + (error.code || error.message) + ')'; }
  if (!bytes.length) return 'empty';
  if (kind === 'png' && (bytes.length < 8 || !bytes.subarray(0, 8).equals(PNG))) return 'invalid PNG signature';
  if (kind === 'trace') {
    if (bytes.length < 30 || !bytes.subarray(0, 4).equals(ZIP_LOCAL)) return 'invalid ZIP local header';
    const tail = bytes.subarray(Math.max(0, bytes.length - 65557));
    if (tail.lastIndexOf(ZIP_END) < 0) return 'missing ZIP end marker';
  }
  return null;
}

export function auditEvidence({ directory, rows, expectedCount }) {
  const issues = [];
  if (!Array.isArray(rows)) return { status: 'INCOMPLETE', issues: ['results: not an array'] };
  if (rows.length !== expectedCount) issues.push('results: expected ' + expectedCount + ' rows, found ' + rows.length);
  const seen = new Set();
  for (const row of rows) {
    if (!row || typeof row.tag !== 'string' || !/^[a-z0-9-]+$/.test(row.tag)) {
      issues.push('results: invalid case tag'); continue;
    }
    if (seen.has(row.tag)) issues.push(row.tag + ': duplicate case');
    seen.add(row.tag);
    if (row.traceError) issues.push(row.tag + ': traceError=' + row.traceError);
    if (row.screenshotError) issues.push(row.tag + ': screenshotError=' + row.screenshotError);
    for (const [name, kind] of [[row.tag + '.zip', 'trace'], [row.tag + '.png', 'png']]) {
      const error = inspectFile(join(directory, name), kind);
      if (error) issues.push(name + ': ' + error);
    }
  }
  for (const name of ['identity.json', 'results.json', 'transport.jsonl']) {
    const error = inspectFile(join(directory, name), 'nonempty');
    if (error) issues.push(name + ': ' + error);
  }
  return { status: issues.length ? 'INCOMPLETE' : 'COMPLETE', issues };
}

export function outcome({ transportSuccess, evidenceStatus }) {
  if (evidenceStatus !== 'COMPLETE') return { status: 'INCOMPLETE', exitCode: 2 };
  if (!transportSuccess) return { status: 'FAIL', exitCode: 1 };
  return { status: 'PASS', exitCode: 0 };
}
