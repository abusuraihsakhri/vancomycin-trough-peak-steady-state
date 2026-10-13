import test from 'node:test';
import assert from 'node:assert/strict';
import {calculatePK, concentrationAtTime} from './pk.mjs';

const input = {dose_mg: 1000, interval_h: 12, infusion_h: 1, elimination_rate_h: 0.1, volume_l: 50, sample_after_infusion_h: 11};

test('reference example and mass balance', () => {
  const r = calculatePK(input);
  assert.ok(Math.abs(r.auc24_mg_h_l - 400) < 1e-10);
  assert.ok(Math.abs(r.peak_mg_l - 27.23577382621341) < 1e-10);
  assert.ok(Math.abs(r.trough_mg_l - 9.06600154888745) < 1e-10);
  assert.ok(Math.abs(r.sample_mg_l - r.trough_mg_l) < 1e-10);
  assert.ok(Math.abs(concentrationAtTime(input, 0) - r.trough_mg_l) < 1e-10);
  assert.ok(Math.abs(concentrationAtTime(input, 1) - r.peak_mg_l) < 1e-10);
  assert.ok(Math.abs(concentrationAtTime(input, 12) - r.trough_mg_l) < 1e-10);
});

test('continuous infusion limit', () => {
  const r = calculatePK({...input, infusion_h: 12, sample_after_infusion_h: 0});
  assert.ok(Math.abs(r.peak_mg_l - r.trough_mg_l) < 1e-10);
});

test('invalid values fail closed', () => {
  for (const patch of [{dose_mg: 0}, {volume_l: NaN}, {infusion_h: 13}, {sample_after_infusion_h: 12}, {elimination_rate_h: 1e-300, volume_l: 1e-300}]) {
    assert.throws(() => calculatePK({...input, ...patch}));
  }
});
