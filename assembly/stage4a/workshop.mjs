// Stage 4-A second delivery: transactional edits of the existing v2 contract.
import {loadAssembly, saveAssembly, placeAtPort} from './contract.mjs';
import {canonicalJson} from './json-data.mjs';

const fail = message => { throw new Error(message); };
const copy = value => JSON.parse(canonicalJson(value));
const endpoint = (instance_id, port) => ({instance_id, port});
const same = (a,b) => a.instance_id === b.instance_id && a.port === b.port;
const incident = (c,id) => c.a.instance_id === id || c.b.instance_id === id;
const find = (a,id) => a.instances.find(i => i.id === id) ?? fail('unknown instance');
const requireKeys = (o,keys) => {
  if (!o || typeof o !== 'object' || Array.isArray(o) ||
      Object.keys(o).length !== keys.length ||
      !keys.every(k => Object.hasOwn(o,k))) fail('invalid edit fields');
};

// CAD Z-up -> glTF Y-up. Apply only to the placement, not the GLB vertices.
export function displayPlacement(instance) {
  const [x,y,z] = instance.translation_m;
  return {position:[x,z,y === 0 ? 0 : -y], yaw:instance.yaw_quarters * Math.PI / 2};
}

export async function editAssembly(catalog, assembly, command) {
  // Snapshot inputs before the first await. No caller object is mutated.
  const c = copy(catalog), op = copy(command), raw = canonicalJson(assembly);
  const a = await loadAssembly(c, raw);
  switch (op.kind) {
    case 'add': {
      requireKeys(op,['kind','id','definition_id','translation_m','yaw_quarters']);
      const d = c.definitions.find(d => d.id === op.definition_id) ?? fail('unknown definition');
      a.instances.push({id:op.id,definition_id:d.id,revision:d.revision,pose:d.pose,
        translation_m:op.translation_m,yaw_quarters:op.yaw_quarters});
      break;
    }
    case 'move': {
      requireKeys(op,['kind','id','translation_m']);
      find(a,op.id).translation_m = op.translation_m;
      break;
    }
    case 'rotate': {
      requireKeys(op,['kind','id','yaw_quarters']);
      find(a,op.id).yaw_quarters = op.yaw_quarters;
      break;
    }
    case 'remove': {
      requireKeys(op,['kind','id']);
      find(a,op.id);
      if (a.connections.some(c => incident(c,op.id))) fail('disconnect before deleting');
      a.instances = a.instances.filter(i => i.id !== op.id);
      break;
    }
    case 'connect':
    case 'align-connect': {
      requireKeys(op,['kind','a','b']);
      requireKeys(op.a,['instance_id','port']); requireKeys(op.b,['instance_id','port']);
      const fixed = find(a,op.a.instance_id), moving = find(a,op.b.instance_id);
      if (op.kind === 'align-connect') {
        if (a.connections.some(c => incident(c,moving.id))) fail('moving part must be disconnected');
        const aligned = placeAtPort(c,fixed,op.a.port,moving,op.b.port);
        a.instances = a.instances.map(i => i.id === moving.id ? aligned : i);
      }
      a.connections.push({a:endpoint(op.a.instance_id,op.a.port),b:endpoint(op.b.instance_id,op.b.port)});
      break;
    }
    case 'disconnect': {
      requireKeys(op,['kind','a','b']);
      requireKeys(op.a,['instance_id','port']); requireKeys(op.b,['instance_id','port']);
      const index = a.connections.findIndex(c => (same(c.a,op.a)&&same(c.b,op.b)) ||
          (same(c.a,op.b)&&same(c.b,op.a)));
      if (index < 0) fail('unknown connection');
      a.connections.splice(index,1);
      break;
    }
    default: fail('unknown edit');
  }
  return loadAssembly(c, await saveAssembly(c,a));
}

// A last-request-wins session for asynchronous UI preparation. A stale
// validation or asset preparation result must never replace current state.
// prepare must not publish to the DOM; it returns staged render data.
export function createWorkshopSession(catalog, initial) {
  const c = copy(catalog);
  let current, epoch = 0;
  const ready = loadAssembly(c,canonicalJson(initial)).then(a => {current = a;});
  const snapshot = () => {
    if (!current) fail('session not ready');
    return copy(current);
  };
  async function submit(produce, prepare = async () => null) {
    const ticket = ++epoch;
    await ready;
    try {
      const next = await produce(snapshot());
      if (ticket !== epoch) return {status:'STALE'};
      const staged = await prepare(copy(next));
      if (ticket !== epoch) return {status:'STALE'};
      current = next;
      return {status:'APPLIED',assembly:snapshot(),staged};
    } catch (error) {
      if (ticket !== epoch) return {status:'STALE'};
      throw error;
    }
  }
  return {
    ready,snapshot,
    edit(command,prepare) {
      const op = copy(command);
      return submit(a => editAssembly(c,a,op),prepare);
    },
    load(text,prepare) { return submit(() => loadAssembly(c,text),prepare); },
    async save() { await ready; return saveAssembly(c,snapshot()); }
  };
}
