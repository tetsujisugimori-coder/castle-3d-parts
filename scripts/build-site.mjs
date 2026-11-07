import { cp, mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
await rm(resolve(root, "dist"), { recursive: true, force: true });
await cp(resolve(root, "site"), resolve(root, "dist"), { recursive: true });
await mkdir(resolve(root, "dist/data"), { recursive: true });
await cp(resolve(root, "catalog/wooden-palisade-v0.json"), resolve(root, "dist/data/wooden-palisade-v0.json"));
console.log("Built dist/ with catalog metadata");