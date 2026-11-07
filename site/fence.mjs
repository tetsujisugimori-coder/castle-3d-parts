// Geometry measurements in metres. No rendering or dependencies.
export function validateFence(raw) {
  const p = {
    count: Number(raw.count),
    height: Number(raw.height),
    spacing: Number(raw.spacing),
    post_width: Number(raw.post_width),
    rails: Number(raw.rails)
  };
  const limits = {
    count: [2, 30],
    height: [0.6, 5],
    spacing: [0.4, 3],
    post_width: [0.08, 0.35],
    rails: [0, 4]
  };
  for (const [name, [min, max]] of Object.entries(limits)) {
    if (!Number.isFinite(p[name]) || p[name] < min || p[name] > max) {
      throw new RangeError(name + " must be from " + min + " to " + max);
    }
  }
  if (!Number.isInteger(p.count) || !Number.isInteger(p.rails)) {
    throw new TypeError("count and rails must be integers");
  }
  if (p.spacing <= p.post_width) throw new RangeError("spacing must exceed post width");
  return p;
}
export function layoutFence(raw) {
  const p = validateFence(raw);
  const width = (p.count - 1) * p.spacing + p.post_width;
  const tipHeight = p.height * 0.14;
  const shaftHeight = p.height - tipHeight;
  const postCenters = Array.from({ length: p.count }, (_, i) =>
    (i - (p.count - 1) / 2) * p.spacing
  );
  const railHeights = Array.from({ length: p.rails }, (_, i) =>
    p.height * (0.32 + (i + 1) * 0.42 / (p.rails + 1))
  );
  return { params: p, width, tipHeight, shaftHeight, postCenters, railHeights };
}