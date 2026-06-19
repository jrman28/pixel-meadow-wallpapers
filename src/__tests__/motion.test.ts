import assert from "node:assert/strict";
import {describe, it} from "node:test";
import {
  LOOP_FRAMES,
  cloudDisplacementPx,
  cloudInfluence,
  grassDisplacementPx,
  moonGlow,
  starTwinkle,
} from "../motion";

describe("wallpaper motion", () => {
  it("returns every animated system to the same state at the loop boundary", () => {
    for (const frame of [0, 17, 181, 359, 719]) {
      assert.equal(
        grassDisplacementPx(frame, 0.37, 0.92),
        grassDisplacementPx(frame + LOOP_FRAMES, 0.37, 0.92),
      );
      assert.deepEqual(
        cloudDisplacementPx(frame, 4, 0.75),
        cloudDisplacementPx(frame + LOOP_FRAMES, 4, 0.75),
      );
      assert.equal(starTwinkle(frame, 9), starTwinkle(frame + LOOP_FRAMES, 9));
      assert.equal(moonGlow(frame), moonGlow(frame + LOOP_FRAMES));
    }
  });

  it("anchors grass roots, sways the tips, and leaves the midground still", () => {
    let observedTipMotion = false;
    for (let frame = 0; frame < LOOP_FRAMES; frame += 7) {
      assert.equal(grassDisplacementPx(frame, 0.5, 0), 0);
      assert.equal(grassDisplacementPx(frame, 0.5, 0.4), 0);
      const tipMotion = grassDisplacementPx(frame, 0.5, 0.2);
      observedTipMotion ||= tipMotion !== 0;
      assert.ok(Math.abs(tipMotion) <= 8);
    }
    assert.equal(observedTipMotion, true);
  });

  it("moves near cloud regions farther than distant cloud regions", () => {
    const distant = cloudDisplacementPx(173, 2, 0.1);
    const near = cloudDisplacementPx(173, 2, 1);
    assert.ok(Math.abs(near.x) >= Math.abs(distant.x));
    assert.ok(Math.abs(near.x) <= 18);
    assert.ok(Math.abs(near.y) <= 2);
  });

  it("fades cloud deformation smoothly to zero outside each ellipse", () => {
    assert.equal(cloudInfluence(0, 0), 1);
    assert.ok(cloudInfluence(0.5, 0) > 0);
    assert.equal(cloudInfluence(1, 0), 0);
    assert.equal(cloudInfluence(1.1, 0), 0);
    assert.equal(cloudInfluence(0, 1.1), 0);
  });

  it("keeps night luminance changes restrained", () => {
    for (let frame = 0; frame < LOOP_FRAMES; frame += 11) {
      const star = starTwinkle(frame, 3);
      assert.ok(star >= 0.72 && star <= 1);
      const moon = moonGlow(frame);
      assert.ok(moon >= 0.96 && moon <= 1.02);
    }
  });
});
