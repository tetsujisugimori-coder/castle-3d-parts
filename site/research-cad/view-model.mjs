// Pure formatting and contract checks. No HTML from research data is executed.
export function validateData(data) {
  if (!data || typeof data !== 'object' || !data.part || typeof data.part !== 'object' ||
      !data.snapshot || typeof data.snapshot !== 'object' || !Array.isArray(data.candidates) ||
      !data.manifest || typeof data.manifest !== 'object') throw new Error('研究データの形式が不正です');
  return data;
}
export function display(value) {
  return value === undefined || value === null ? '未設定 / 未確認' : typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
}
export function candidateLabel(candidate, index) {
  return `${candidate.id ?? candidate.candidate_id ?? `候補 ${index + 1}`} · ${candidate.status ?? '状態未記録'}`;
}
