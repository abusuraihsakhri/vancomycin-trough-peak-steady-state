/** One-compartment steady-state repeated IV infusion; illustrative model only. */
export function calculatePK(values) {
  const required = ['dose_mg', 'interval_h', 'infusion_h', 'elimination_rate_h', 'volume_l'];
  const p = {};
  for (const key of required) {
    if (values[key] === '' || values[key] === null || values[key] === undefined) {
      throw new Error(`${key} is required`);
    }
    p[key] = Number(values[key]);
    if (!Number.isFinite(p[key]) || p[key] <= 0) {
      throw new Error(`${key} must be a finite number greater than zero`);
    }
  }
  const postValue = values.sample_after_infusion_h ?? 0;
  if (postValue === '') throw new Error('sample_after_infusion_h must be specified');
  const post = Number(postValue);
  if (!Number.isFinite(post) || post < 0) throw new Error('sample_after_infusion_h must be finite and nonnegative');
  const {dose_mg: dose, interval_h: tau, infusion_h: tin, elimination_rate_h: kel, volume_l: vd} = p;
  if (tin > tau) throw new Error('Infusion duration cannot exceed the dosing interval');
  if (post > tau - tin) throw new Error('Sample time must fall before the next dose');
  const cl = kel * vd;
  if (!Number.isFinite(cl) || cl === 0 || tin * cl === 0) throw new Error('Inputs produce non-finite PK outputs');
  const peak = (dose / (tin * cl)) * (-Math.expm1(-kel * tin) / -Math.expm1(-kel * tau));
  const trough = peak * Math.exp(-kel * (tau - tin));
  const result = {
    clearance_l_h: cl,
    half_life_h: Math.LN2 / kel,
    peak_mg_l: peak,
    trough_mg_l: trough,
    sample_mg_l: peak * Math.exp(-kel * post),
    auc24_mg_h_l: 24 * dose / (tau * cl),
    approx_steady_state_h: 5 * Math.LN2 / kel,
  };
  if (Object.values(result).some(value => !Number.isFinite(value))) {
    throw new Error('Inputs produce non-finite PK outputs');
  }
  return result;
}

export function concentrationAtTime(values, time) {
  const r = calculatePK(values);
  const t = Number(time);
  const tau = Number(values.interval_h);
  const tin = Number(values.infusion_h);
  const kel = Number(values.elimination_rate_h);
  const dose = Number(values.dose_mg);
  if (!Number.isFinite(t) || t < 0 || t > tau) throw new Error('Time outside dosing interval');
  if (t <= tin) {
    const inputRateOverClearance = dose / (tin * r.clearance_l_h);
    return r.trough_mg_l * Math.exp(-kel * t) + inputRateOverClearance * (-Math.expm1(-kel * t));
  }
  return r.peak_mg_l * Math.exp(-kel * (t - tin));
}
