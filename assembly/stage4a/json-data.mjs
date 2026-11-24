function ownData(object, key) {
  const entry = Object.getOwnPropertyDescriptor(object, key);
  if (!entry?.enumerable || !Object.hasOwn(entry, "value")) {
    throw new Error("expected own JSON data property");
  }
  return entry.value;
}

export function canonicalJson(value) {
  const ancestors = new Set();

  function encode(item) {
    if (item === null || typeof item === "string" || typeof item === "boolean") {
      return JSON.stringify(item);
    }
    if (typeof item === "number" && Number.isFinite(item)) {
      return JSON.stringify(item);
    }
    if (typeof item !== "object" || ancestors.has(item) || ancestors.size >= 64) {
      throw new Error("expected finite, acyclic JSON data with at most 64 container levels");
    }

    ancestors.add(item);
    try {
      const keys = Reflect.ownKeys(item);
      if (Array.isArray(item)) {
        if (keys.length !== item.length + 1) {
          throw new Error("expected dense JSON array");
        }
        const elements = [];
        for (let index = 0; index < item.length; index++) {
          elements.push(encode(ownData(item, index)));
        }
        return "[" + elements.join(",") + "]";
      }

      const prototype = Object.getPrototypeOf(item);
      if ((prototype !== Object.prototype && prototype !== null) ||
          keys.some(key => typeof key !== "string")) {
        throw new Error("expected plain JSON object");
      }
      const members = keys.sort().map(key =>
        JSON.stringify(key) + ":" + encode(ownData(item, key))
      );
      return "{" + members.join(",") + "}";
    } finally {
      ancestors.delete(item);
    }
  }

  return encode(value);
}

export function parseUniqueJson(text) {
  const value = JSON.parse(text);
  // The parser has already checked the grammar. Walk the tokens to find keys
  // that JSON.parse would otherwise silently replace.
  const containers = [];
  for (let index = 0; index < text.length; index++) {
    const token = text[index];
    if (token === "{") {
      containers.push({ keys: new Set(), expectKey: true });
    } else if (token === "[") {
      containers.push(null);
    } else if (token === "}" || token === "]") {
      containers.pop();
    } else if (token === "," && containers.at(-1)) {
      containers.at(-1).expectKey = true;
    } else if (token === '"') {
      const start = index++;
      while (text[index] !== '"') {
        if (text[index] === "\\") index++;
        index++;
      }
      const object = containers.at(-1);
      if (object?.expectKey) {
        const key = JSON.parse(text.slice(start, index + 1));
        if (object.keys.has(key)) throw new Error("duplicate JSON key: " + key);
        object.keys.add(key);
        object.expectKey = false;
      }
    }
  }
  return value;
}
