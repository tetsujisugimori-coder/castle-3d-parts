// Dependency-free strict subset of JSON Schema 2020-12. Unsupported keywords fail closed.
const keywords = new Set(['$schema','$id','title','type','const','enum','properties','required','additionalProperties','items','minItems','uniqueItems','minLength','pattern','minimum','maximum','format']);
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const canonical = x => Array.isArray(x) ? '['+x.map(canonical).join(',')+']' : plain(x) ? '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}' : JSON.stringify(x);
export function validateSupportedSchema(spec) {
  if (!plain(spec)) throw Error('SCHEMA_OBJECT');
  for (const key of Object.keys(spec)) if (!keywords.has(key)) throw Error(`SCHEMA_UNSUPPORTED ${key}`);
  if ('$schema' in spec && spec.$schema !== 'https://json-schema.org/draft/2020-12/schema') throw Error('SCHEMA_DIALECT');
  for (const key of ['$id','title','pattern']) if (key in spec && typeof spec[key]!=='string') throw Error(`SCHEMA_VALUE ${key}`);
  if (spec.pattern) new RegExp(spec.pattern);
  if ('type' in spec && (![].concat(spec.type).length || ![].concat(spec.type).every(x=>['null','array','object','integer','number','string','boolean'].includes(x)))) throw Error('SCHEMA_TYPE');
  if ('format' in spec && !['uri','date'].includes(spec.format)) throw Error('SCHEMA_FORMAT');
  for (const key of ['additionalProperties','uniqueItems']) if (key in spec && typeof spec[key]!=='boolean') throw Error(`SCHEMA_VALUE ${key}`);
  for (const key of ['minItems','minLength']) if (key in spec && (!Number.isSafeInteger(spec[key]) || spec[key]<0)) throw Error(`SCHEMA_VALUE ${key}`);
  for (const key of ['minimum','maximum']) if (key in spec && !Number.isFinite(spec[key])) throw Error(`SCHEMA_VALUE ${key}`);
  if ('required' in spec && (!Array.isArray(spec.required) || !spec.required.every(x=>typeof x==='string'))) throw Error('SCHEMA_VALUE required');
  if ('enum' in spec && (!Array.isArray(spec.enum) || !spec.enum.length || !spec.enum.every(x=>x===null || ['string','number','boolean'].includes(typeof x)))) throw Error('SCHEMA_VALUE enum');
  if ('const' in spec && spec.const!==null && !['string','number','boolean'].includes(typeof spec.const)) throw Error('SCHEMA_VALUE const');
  if ('properties' in spec && !plain(spec.properties)) throw Error('SCHEMA_VALUE properties');
  for (const child of Object.values(spec.properties ?? {})) validateSupportedSchema(child);
  if ('items' in spec) validateSupportedSchema(spec.items);
}
export function validateSchema(value, spec, path = '$', nested = false) {
  if (!nested) validateSupportedSchema(spec);
  const fail = code => {throw Error(`${code} ${path}`)};
  if ('const' in spec && value !== spec.const) fail('CONST');
  if (spec.type) {
    const types = [].concat(spec.type);
    const matches = t => t === 'null' ? value === null : t === 'array' ? Array.isArray(value) : t === 'object' ? value !== null && !Array.isArray(value) && typeof value === 'object' : t === 'integer' ? Number.isSafeInteger(value) : t === 'number' ? typeof value === 'number' && Number.isFinite(value) : typeof value === t;
    if (!types.some(matches)) fail('TYPE');
  }
  if (spec.enum && !spec.enum.includes(value)) fail('ENUM');
  if (typeof value === 'string') {
    if (spec.minLength && value.trim().length < spec.minLength) fail('EMPTY');
    if (spec.pattern && !new RegExp(spec.pattern).test(value)) fail('PATTERN');
    if (spec.format === 'uri') { try { const u = new URL(value); if (!['http:','https:'].includes(u.protocol) || u.username || u.password || /\s/.test(value)) fail('URL'); } catch {fail('URL')} }
    if (spec.format === 'date' && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value)) fail('DATE');
    if (spec.format && !['uri','date'].includes(spec.format)) fail('SCHEMA_FORMAT');
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) fail('NUMBER');
    if (spec.minimum !== undefined && value < spec.minimum) fail('MINIMUM');
    if (spec.maximum !== undefined && value > spec.maximum) fail('MAXIMUM');
  }
  if (Array.isArray(value)) {
    if (spec.minItems && value.length < spec.minItems) fail('MIN_ITEMS');
    if (spec.uniqueItems && new Set(value.map(canonical)).size !== value.length) fail('DUPLICATE_ITEM');
    value.forEach((x,i) => validateSchema(x,spec.items,`${path}[${i}]`,true));
  } else if (value !== null && typeof value === 'object') {
    for (const k of spec.required ?? []) if (!Object.hasOwn(value,k)) fail(`MISSING:${k}`);
    for (const k of Object.keys(value)) {
      if (!Object.hasOwn(spec.properties ?? {}, k)) {if (spec.additionalProperties === false) fail(`EXTRA:${k}`)}
      else validateSchema(value[k],spec.properties[k],`${path}.${k}`,true);
    }
  }
}
