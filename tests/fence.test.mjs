import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { layoutFence, validateFence } from "../site/fence.mjs";
const source = JSON.parse(readFileSync(new URL("../catalog/wooden-palisade-v0.json", import.meta.url), "utf8"));
const defaults = source.dimensions_m;
test("initial wood fence has 5 posts, 2 rails and a total width of 4.95m", () => {
  const model = layoutFence(defaults);
  assert.equal(model.postCenters.length, 5);
  assert.equal(model.railHeights.length, 2);
  assert.equal(model.params.height, 2);
  assert.ok(Math.abs(model.width - 4.95) < 1e-9);
  assert.ok(Math.abs(model.postCenters[0] + 2.4) < 1e-9);
  assert.ok(Math.abs(model.postCenters[4] - 2.4) < 1e-9);
  assert.ok(Math.abs(model.shaftHeight + model.tipHeight - 2) < 1e-9);
});
test("new count and spacing update the width symmetrically", () => {
  const model = layoutFence({ ...defaults, count: 9, spacing: 0.9 });
  assert.ok(Math.abs(model.width - 7.35) < 1e-9);
  assert.ok(Math.abs(model.postCenters[0] + model.postCenters.at(-1)) < 1e-9);
});
test("zero rails is allowed", () => {
  assert.deepEqual(layoutFence({ ...defaults, rails: 0 }).railHeights, []);
});
test("invalid dimensions are rejected", () => {
  assert.throws(() => validateFence({ ...defaults, height: 0 }), RangeError);
  assert.throws(() => validateFence({ ...defaults, spacing: 0.1 }), RangeError);
  assert.throws(() => validateFence({ ...defaults, count: 2.5 }), TypeError);
  assert.throws(() => validateFence({ ...defaults, count: Infinity }), RangeError);
});
test("unverified historical claims stay marked as unverified", () => {
  assert.equal(source.evidence.existence_at_yamanaka.status, "unverified");
  assert.equal(source.evidence.shape_and_dimensions.status, "hypothetical");
  assert.equal(source.evidence.analogues_at_other_castles.status, "not_researched");
  assert.deepEqual(source.evidence.existence_at_yamanaka.sources, []);
});