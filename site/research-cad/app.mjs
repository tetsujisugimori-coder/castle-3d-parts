import {validateData, display, candidateLabel} from './view-model.mjs';
const status = document.querySelector('#status');
function element(tag, text) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node; }
function values(host, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) { host.append(element('pre', display(value))); return; }
  const list = element('dl');
  for (const [key, val] of Object.entries(value)) {
    list.append(element('dt', key)); const detail = element('dd');
    const formatted = display(val);
    const content = element(typeof val === 'object' && val !== null ? 'pre' : 'span', formatted);
    if (formatted.length > 2000) {
      const disclosure = element('details'); disclosure.append(element('summary', `${key} の詳細を表示`), content); detail.append(disclosure);
    } else detail.append(content);
    list.append(detail);
  }
  host.append(list);
}
try {
  const response = await fetch('./data.json', {cache:'no-store'});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = validateData(await response.json());
  values(document.querySelector('#part'), data.part);
  const research = document.querySelector('#research');
  for (const [key, value] of Object.entries(data.snapshot)) {
    research.append(element('h3', key));
    if (Array.isArray(value)) {
      if (!value.length) research.append(element('p', '記録なし'));
      value.forEach((record, index) => {
        const item = element('details');
        const label = record && typeof record === 'object' ? `${record.id ?? `${record.from ?? ''} → ${record.to ?? ''}`} · ${record.kind ?? record.relation ?? ''} ${record.status ?? ''}` : String(index + 1);
        item.append(element('summary', label)); values(item, record); research.append(item);
      });
    } else values(research, value);
  }
  values(document.querySelector('#execution'), data.manifest);
  const select = document.querySelector('#candidate'), detail = document.querySelector('#candidate-detail');
  data.candidates.forEach((candidate, i) => { const option = element('option', candidateLabel(candidate, i)); option.value = String(i); select.append(option); });
  const show = () => {
    detail.replaceChildren(); const candidate = data.candidates[Number(select.value)];
    if (!candidate) { detail.append(element('p', '確認できる変更候補はありません。')); return; }
    detail.append(element('p', '閲覧中の候補です。承認・適用は行っていません。'));
    if (Array.isArray(candidate.parameter_changes)) {
      detail.append(element('h3', 'パラメータ差分（試作D）'));
      for (const change of candidate.parameter_changes) {
        detail.append(element('h4', display(change.parameter)));
        const columns = element('div'); columns.className = 'columns';
        for (const [label, value] of [['変更前', change.current_value], ['変更候補', change.proposed_value]]) {
          const column = element('div'); column.append(element('strong', label));
          column.append(element('pre', `${display(value)} ${change.unit ?? ''}`)); columns.append(column);
        }
        detail.append(columns);
      }
    }
    if (Array.isArray(candidate.evidence_changes)) {
      detail.append(element('h3', '研究根拠の差分'));
      if (!candidate.evidence_changes.length) detail.append(element('p', '根拠の変更はありません。'));
      for (const change of candidate.evidence_changes) {
        detail.append(element('h4', display(change.id)));
        const columns = element('div'); columns.className = 'columns';
        for (const [label, value] of [['変更前', change.before], ['変更候補', change.after]]) {
          const column = element('div'); column.append(element('strong', label));
          column.append(element('pre', display(value))); columns.append(column);
        }
        detail.append(columns);
      }
    }
    const metadata = Object.fromEntries(Object.entries(candidate).filter(([key]) => !['parameter_changes', 'evidence_changes'].includes(key)));
    detail.append(element('h3', '候補の状態と根拠区分')); values(detail, metadata);
  };
  select.disabled = data.candidates.length === 0; select.addEventListener('change', show); show();
  document.querySelector('#data-panels').hidden = false;
  status.textContent = '研究データを読み込みました。閲覧専用・正式採用なし。'; status.dataset.loaded = 'true';
} catch (error) {
  status.textContent = `研究データを読み込めません。再読み込みするか生成データを確認してください。詳細: ${error.message}`;
  status.dataset.error = 'true'; status.setAttribute('role', 'alert');
}
