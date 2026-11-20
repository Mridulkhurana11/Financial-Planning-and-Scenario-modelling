import { useEffect, useMemo, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart,
  Line, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import {
  Activity, ArrowDownRight, ArrowUpRight, BarChart3, BriefcaseBusiness,
  CalendarDays, ChevronDown, CircleHelp, Download, FileSpreadsheet,
  Gauge, Menu, Settings2, ShieldCheck, Sparkles, TrendingUp, Wallet, X,
} from 'lucide-react'

const NAV = [
  { id: 'overview', label: 'Revenue forecast', icon: LayoutIcon },
  { id: 'scenarios', label: 'Scenario planning', icon: TrendingUp },
  { id: 'segments', label: 'Business lines', icon: BriefcaseBusiness },
  { id: 'model', label: 'Model & data', icon: ShieldCheck },
]
function LayoutIcon({ size = 18 }) { return <BarChart3 size={size} /> }

const PRESETS = {
  'Base case': { demand_growth_pct: 0, price_mix_pct: 0, contribution_margin_pct: 26, operating_expense_pct: 12 },
  'Upside': { demand_growth_pct: 4, price_mix_pct: 1, contribution_margin_pct: 27.5, operating_expense_pct: 11.5 },
  'Conservative': { demand_growth_pct: -3, price_mix_pct: -0.5, contribution_margin_pct: 24, operating_expense_pct: 13 },
}
const PRESET_COPY = {
  'Base case': 'Model baseline with measured planning assumptions.',
  'Upside': 'Stronger demand with improved price and mix realisation.',
  'Conservative': 'Softer demand with additional operating cost pressure.',
}
const COLORS = ['#147b72', '#79aaa0', '#d6ae68', '#8095ae', '#c77a63']

const money = (v, compact = false) => {
  const n = Number(v || 0)
  if (compact && Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (compact && Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (compact && Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}
const whole = (v) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(v || 0))
const pct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`
const fmtDate = (s) => new Date(`${s}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
const fmtMonth = (s) => new Date(`${s}T00:00:00`).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })

function Metric({ label, value, note, icon: Icon, tint = 'teal', trend }) {
  return <div className="metric-card">
    <div className="metric-head"><span>{label}</span><span className={`metric-icon ${tint}`}><Icon size={16} /></span></div>
    <div className="metric-value">{value}</div>
    <div className="metric-note"><span>{note}</span>{trend && <b className={trend.startsWith('-') ? 'negative' : 'positive'}>{trend}</b>}</div>
  </div>
}

function Panel({ title, subtitle, action, children, className = '' }) {
  return <section className={`panel ${className}`}>
    <div className="panel-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>
    {children}
  </section>
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const visible = payload.filter(p => p.value !== undefined && p.value !== null && !String(p.dataKey).includes('range'))
  return <div className="chart-tooltip"><div className="tooltip-date">{fmtDate(label)}</div>
    {visible.map((p, i) => <div className="tooltip-line" key={`${p.dataKey}-${i}`}><i style={{ background: p.color || p.fill }} /><span>{p.name}</span><b>{money(p.value)}</b></div>)}
  </div>
}

function ForecastChart({ data }) {
  const chart = useMemo(() => {
    const history = data.historical_weekly.map(r => ({ date: r.Date, actual: r.actual_sales, forecast: null, plan: null, rangeBase: null, rangeBand: null }))
    const future = data.forecast.map(r => ({
      date: r.Date, actual: null, forecast: r.revenue, plan: r.reference_plan,
      rangeBase: r.revenue * (1 - data.bandPct), rangeBand: r.revenue * data.bandPct * 2,
    }))
    return [...history, ...future]
  }, [data])
  const ticks = chart.filter((r, i) => i % 8 === 0 || i === chart.length - 1).map(r => r.date)
  return <div className="forecast-chart">
    <div className="chart-legend">
      <span><i className="legend-actual" />Actuals</span>
      <span><i className="legend-plan" />Reference plan</span>
      <span><i className="legend-forecast" />Selected forecast</span>
      <span><i className="legend-band" />Backtest error band</span>
    </div>
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chart} margin={{ top: 12, right: 14, left: 2, bottom: 4 }}>
        <defs><linearGradient id="forecastArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#147b72" stopOpacity={0.18} /><stop offset="100%" stopColor="#147b72" stopOpacity={0.015} /></linearGradient></defs>
        <CartesianGrid vertical={false} stroke="#e9eeee" strokeDasharray="3 5" />
        <XAxis dataKey="date" ticks={ticks} tickFormatter={fmtMonth} axisLine={false} tickLine={false} tick={{ fill: '#87969a', fontSize: 9 }} dy={8} />
        <YAxis tickFormatter={v => money(v, true)} axisLine={false} tickLine={false} width={64} tick={{ fill: '#87969a', fontSize: 9 }} />
        <Tooltip content={<ChartTooltip />} />
        <Area dataKey="rangeBase" stackId="range" stroke="none" fill="transparent" isAnimationActive={false} legendType="none" />
        <Area dataKey="rangeBand" stackId="range" stroke="none" fill="#dbeae5" fillOpacity={0.8} isAnimationActive={false} legendType="none" />
        <Area dataKey="forecast" type="monotone" stroke="#147b72" strokeWidth={2.5} fill="url(#forecastArea)" connectNulls activeDot={{ r: 4, fill: '#147b72', strokeWidth: 0 }} />
        <Line dataKey="actual" type="monotone" stroke="#176c69" strokeWidth={2.1} dot={false} connectNulls={false} />
        <Line dataKey="plan" type="monotone" stroke="#91a4a4" strokeWidth={1.7} strokeDasharray="6 5" dot={false} connectNulls />
      </ComposedChart>
    </ResponsiveContainer>
  </div>
}

function ScenarioSidePanel({ selected, setSelected, assumptions, setAssumptions, metadata }) {
  const drivers = [
    { key: 'demand_growth_pct', label: 'Demand / volume growth', min: -10, max: 15, step: 0.5, unit: '%' },
    { key: 'price_mix_pct', label: 'Price / mix realisation', min: -5, max: 8, step: 0.5, unit: '%' },
    { key: 'contribution_margin_pct', label: 'Contribution margin assumption', min: 10, max: 45, step: 0.5, unit: '%' },
    { key: 'operating_expense_pct', label: 'Operating expense assumption', min: 4, max: 25, step: 0.5, unit: '%' },
  ]
  return <div className="scenario-controls">
    <div className="section-caption">SCENARIO</div>
    {Object.keys(PRESETS).map((name, i) => <button key={name} className={`scenario-choice ${selected === name ? 'selected' : ''}`} onClick={() => { setSelected(name); setAssumptions({ ...PRESETS[name] }) }}>
      <span className={`scenario-symbol ${['base', 'upside', 'downside'][i]}`}>{i === 0 ? '●' : i === 1 ? '↗' : '↘'}</span>
      <span><b>{name}</b><small>{PRESET_COPY[name]}</small></span>
    </button>)}
    <div className="driver-title"><div className="section-caption">KEY DRIVERS</div><Settings2 size={14} /></div>
    {drivers.map(d => <label className="driver-control" key={d.key}>
      <span className="driver-label">{d.label}<b>{Number(assumptions[d.key]).toFixed(1)}{d.unit}</b></span>
      <input type="range" min={d.min} max={d.max} step={d.step} value={assumptions[d.key]} onChange={e => { setSelected('Custom'); setAssumptions(a => ({ ...a, [d.key]: Number(e.target.value) })) }} />
    </label>)}
    <div className="assumption-disclaimer">Planning assumptions are editable. Margin and operating expense rates are illustrative — they are not reported in the source dataset.</div>
    <div className="side-source"><div className="source-mark"><ShieldCheck size={15} /></div><div><b>Modelled from source data</b><small>{whole(metadata.historical_rows)} historical store-department weeks</small></div></div>
  </div>
}

function OverviewPage({ data, selected, assumptions, derived, setPage }) {
  const k = derived.kpis
  const segmentRows = data.segments.map(s => {
    const factor = (1 + assumptions.demand_growth_pct / 100) * (1 + assumptions.price_mix_pct / 100)
    const forecast = s.forecast_revenue * factor
    const contribution = forecast * ((assumptions.contribution_margin_pct - assumptions.operating_expense_pct) / 100)
    return { ...s, selected_forecast: forecast, contribution }
  })
  return <>
    <div className="kpi-grid">
      <Metric label="Forecast revenue" value={money(k.forecastRevenue, true)} note={`${data.metadata.forecast_weeks} weeks · selected scenario`} icon={Wallet} tint="teal" />
      <Metric label="Plan variance" value={`${k.planVariance >= 0 ? '+' : ''}${money(k.planVariance, true)}`} note={`${k.planVariancePct >= 0 ? '+' : ''}${(k.planVariancePct * 100).toFixed(1)}% vs reference plan`} icon={k.planVariance >= 0 ? ArrowUpRight : ArrowDownRight} tint="blue" trend={`${k.planVariancePct >= 0 ? '+' : ''}${(k.planVariancePct * 100).toFixed(1)}%`} />
      <Metric label="Modelled operating contribution" value={money(k.operatingContribution, true)} note="Forecast revenue × assumed contribution less opex" icon={Activity} tint="gold" />
      <Metric label="Indicative forecast range" value={`${money(k.lower, true)} – ${money(k.upper, true)}`} note={`P90 absolute error from ${data.metrics.validation_weeks}-week backtest`} icon={Gauge} tint="amber" />
    </div>

    <div className="forecast-layout">
      <Panel title="Revenue forecast" subtitle={`Historical actuals and model forecast · ${fmtDate(data.metadata.forecast_start)} – ${fmtDate(data.metadata.forecast_end)}`} className="forecast-panel" action={<span className="unit-label">USD · WEEKLY</span>}>
        <ForecastChart data={derived.chartData} />
        <div className="chart-footnote">Reference plan = same ISO week historical average by store / department × 1.02. Shaded band = P90 absolute weekly percentage error from the recursive holdout backtest; it is not a calibrated confidence interval.</div>
      </Panel>
      <Panel title="Forecast summary" subtitle={selected === 'Custom' ? 'Custom planning assumptions' : PRESET_COPY[selected]} className="summary-panel">
        <div className="summary-primary"><span>Selected forecast</span><b>{money(k.forecastRevenue, true)}</b><small className={k.planVariance >= 0 ? 'positive' : 'negative'}>{k.planVariance >= 0 ? '+' : ''}{money(k.planVariance, true)} vs reference plan</small></div>
        <div className="summary-divider" />
        <div className="summary-row"><span>Reference plan</span><b>{money(k.referencePlan, true)}</b></div>
        <div className="summary-row"><span>Modelled contribution</span><b>{money(k.operatingContribution, true)}</b></div>
        <div className="summary-row"><span>Contribution rate</span><b>{(assumptions.contribution_margin_pct - assumptions.operating_expense_pct).toFixed(1)}%</b></div>
        <div className="summary-note"><Sparkles size={15} /><span>Forecast is generated from a time-aware model. Scenario drivers are applied separately so their effects remain transparent.</span></div>
      </Panel>
    </div>

    <div className="lower-grid">
      <Panel title="Revenue forecast by business line" subtitle="Store format · selected scenario" action={<button className="text-action" onClick={() => setPage('segments')}>View detail <ArrowUpRight size={13} /></button>}>
        <div className="table-scroll"><table className="forecast-table"><thead><tr><th>BUSINESS LINE</th><th>RECENT 13 WK ACTUALS</th><th>REFERENCE PLAN</th><th>SELECTED FORECAST</th><th>VARIANCE</th></tr></thead><tbody>
          {segmentRows.map(row => {
            const recent = data.recent_segment_actuals.find(x => x.Type === row.Type)?.recent_actual || 0
            const variance = row.selected_forecast - row.reference_plan
            return <tr key={row.Type}><td><b>Store type {row.Type}</b><small>{row.stores} stores · {row.departments} departments</small></td><td>{money(recent, true)}</td><td>{money(row.reference_plan, true)}</td><td className="focus-cell">{money(row.selected_forecast, true)}</td><td className={variance >= 0 ? 'positive' : 'negative'}>{variance >= 0 ? '+' : ''}{money(variance, true)}</td></tr>
          })}
        </tbody></table></div>
        <div className="table-footnote">Store types A, B and C are anonymised formats in the source dataset. They are used here as business-line groupings.</div>
      </Panel>
      <Panel title="Planning assumptions" subtitle="Active scenario drivers">
        <div className="driver-summary">
          <div><span>Demand / volume</span><b>{assumptions.demand_growth_pct > 0 ? '+' : ''}{assumptions.demand_growth_pct.toFixed(1)}%</b></div>
          <div><span>Price / mix</span><b>{assumptions.price_mix_pct > 0 ? '+' : ''}{assumptions.price_mix_pct.toFixed(1)}%</b></div>
          <div><span>Contribution margin</span><b>{assumptions.contribution_margin_pct.toFixed(1)}%</b></div>
          <div><span>Operating expense rate</span><b>{assumptions.operating_expense_pct.toFixed(1)}%</b></div>
        </div>
        <button className="outline-button full-button" onClick={() => setPage('scenarios')}>Open scenario planner <ArrowUpRight size={14} /></button>
      </Panel>
    </div>
  </>
}

function ScenarioPage({ data, selected, setSelected, assumptions, setAssumptions, derived }) {
  const [compare, setCompare] = useState(['Base case', 'Upside', 'Conservative'])
  const futureTotal = data.kpis.forecast_revenue_base
  const scenarios = Object.entries(PRESETS).map(([name, p]) => {
    const factor = (1 + p.demand_growth_pct / 100) * (1 + p.price_mix_pct / 100)
    const revenue = futureTotal * factor
    const contribution = revenue * ((p.contribution_margin_pct - p.operating_expense_pct) / 100)
    return { name, revenue, contribution, plan: data.kpis.reference_plan_revenue }
  })
  const toggle = (name) => setCompare(v => v.includes(name) ? v.filter(x => x !== name) : [...v, name])
  return <>
    <div className="page-intro"><div><div className="eyebrow">PLANNING WORKSPACE</div><h2>Scenario planning</h2><p>Compare operating assumptions and understand their effect on revenue and modelled contribution.</p></div><div className="selected-pill"><span>ACTIVE SCENARIO</span><b>{selected}</b></div></div>
    <div className="scenario-grid">
      {Object.keys(PRESETS).map((name, i) => <button className={`scenario-card ${selected === name ? 'active' : ''}`} key={name} onClick={() => { setSelected(name); setAssumptions({ ...PRESETS[name] }) }}><span className={`scenario-card-mark tone-${i}`}>{['●', '↗', '↘'][i]}</span><b>{name}</b><strong>{money(scenarios.find(s => s.name === name).revenue, true)}</strong><small>{PRESET_COPY[name]}</small><i>{selected === name ? 'Currently selected' : 'Select scenario'}</i></button>)}
    </div>
    <div className="two-column">
      <Panel title="Scenario comparison" subtitle="Illustrative revenue outcome across standard assumptions">
        <div className="chart-large"><ResponsiveContainer width="100%" height="100%"><BarChart data={scenarios} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}><CartesianGrid vertical={false} stroke="#e9eeee" strokeDasharray="3 5" /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#75878a', fontSize: 10 }} /><YAxis tickFormatter={v => money(v, true)} axisLine={false} tickLine={false} width={62} tick={{ fill: '#87969a', fontSize: 9 }} /><Tooltip formatter={v => money(v)} /><Bar dataKey="revenue" name="Forecast revenue" radius={[5, 5, 0, 0]}>{scenarios.map((s, i) => <Cell key={s.name} fill={['#147b72', '#8ab4a8', '#d3a96a'][i]} />)}</Bar></BarChart></ResponsiveContainer></div>
      </Panel>
      <Panel title="Current scenario outcome" subtitle="Calculated using the live driver controls">
        <div className="scenario-outcome"><span>Forecast revenue</span><b>{money(derived.kpis.forecastRevenue, true)}</b><small>Variance to plan: {derived.kpis.planVariance >= 0 ? '+' : ''}{money(derived.kpis.planVariance, true)}</small></div>
        <div className="outcome-bars"><div><span>Contribution margin</span><b>{assumptions.contribution_margin_pct.toFixed(1)}%</b><i><em style={{ width: `${assumptions.contribution_margin_pct / 45 * 100}%` }} /></i></div><div><span>Operating expense rate</span><b>{assumptions.operating_expense_pct.toFixed(1)}%</b><i><em className="expense" style={{ width: `${assumptions.operating_expense_pct / 25 * 100}%` }} /></i></div></div>
        <div className="summary-note"><CircleHelp size={15} /><span>These margin and expense rates are adjustable planning assumptions because the source contains no actual cost ledger.</span></div>
      </Panel>
    </div>
    <Panel title="Scenario driver comparison" subtitle="Compare the inputs behind each planning case">
      <div className="table-scroll"><table className="forecast-table"><thead><tr><th>SCENARIO</th><th>DEMAND / VOLUME</th><th>PRICE / MIX</th><th>CONTRIBUTION MARGIN</th><th>OPEX RATE</th><th>MODELLED CONTRIBUTION</th></tr></thead><tbody>{Object.entries(PRESETS).map(([name, p]) => { const row = scenarios.find(x => x.name === name); return <tr key={name}><td><b>{name}</b></td><td>{p.demand_growth_pct > 0 ? '+' : ''}{p.demand_growth_pct.toFixed(1)}%</td><td>{p.price_mix_pct > 0 ? '+' : ''}{p.price_mix_pct.toFixed(1)}%</td><td>{p.contribution_margin_pct.toFixed(1)}%</td><td>{p.operating_expense_pct.toFixed(1)}%</td><td className="focus-cell">{money(row.contribution, true)}</td></tr> })}</tbody></table></div>
    </Panel>
  </>
}

function SegmentPage({ data, assumptions, derived }) {
  const factor = (1 + assumptions.demand_growth_pct / 100) * (1 + assumptions.price_mix_pct / 100)
  const types = data.segments.map(s => ({ ...s, selected_forecast: s.forecast_revenue * factor, contribution: s.forecast_revenue * factor * ((assumptions.contribution_margin_pct - assumptions.operating_expense_pct) / 100) }))
  const quarters = data.segment_quarter.map(r => ({ ...r, selected_forecast: r.forecast_revenue * factor }))
  return <>
    <div className="page-intro"><div><div className="eyebrow">BUSINESS LINE PLANNING</div><h2>Performance by business line</h2><p>Store format A, B and C provide the segment view available in the source data.</p></div></div>
    <div className="kpi-grid compact-grid">
      <Metric label="Business lines" value={whole(types.length)} note="Anonymised store formats" icon={BriefcaseBusiness} />
      <Metric label="Stores covered" value={whole(data.metadata.stores)} note="Across all store types" icon={Activity} tint="blue" />
      <Metric label="Forecast departments" value={whole(data.metadata.departments)} note="Department identifiers" icon={BarChart3} tint="gold" />
      <Metric label="Planning horizon" value={`${data.metadata.forecast_weeks} weeks`} note={`${fmtDate(data.metadata.forecast_start)} – ${fmtDate(data.metadata.forecast_end)}`} icon={CalendarDays} tint="amber" />
    </div>
    <div className="two-column">
      <Panel title="Forecast by store format" subtitle="Selected scenario revenue">
        <div className="chart-large"><ResponsiveContainer width="100%" height="100%"><BarChart data={types} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}><CartesianGrid vertical={false} stroke="#e9eeee" strokeDasharray="3 5" /><XAxis dataKey="Type" tickFormatter={v => `Type ${v}`} axisLine={false} tickLine={false} tick={{ fill: '#75878a', fontSize: 10 }} /><YAxis tickFormatter={v => money(v, true)} axisLine={false} tickLine={false} width={60} tick={{ fill: '#87969a', fontSize: 9 }} /><Tooltip formatter={v => money(v)} /><Bar dataKey="selected_forecast" name="Selected forecast" fill="#167b72" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div>
      </Panel>
      <Panel title="Quarterly planning profile" subtitle="13-week planning blocks across the forecast horizon">
        <div className="chart-large"><ResponsiveContainer width="100%" height="100%"><BarChart data={['Q1', 'Q2', 'Q3', 'Q4'].map(q => { const row = { quarter: q }; types.forEach(t => { row[`Type ${t.Type}`] = quarters.filter(x => x.planning_quarter === q && x.Type === t.Type).reduce((a, x) => a + x.selected_forecast, 0) }); return row })} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}><CartesianGrid vertical={false} stroke="#e9eeee" strokeDasharray="3 5" /><XAxis dataKey="quarter" axisLine={false} tickLine={false} tick={{ fill: '#75878a', fontSize: 10 }} /><YAxis tickFormatter={v => money(v, true)} axisLine={false} tickLine={false} width={60} tick={{ fill: '#87969a', fontSize: 9 }} /><Tooltip formatter={v => money(v)} /><Bar dataKey="Type A" stackId="a" fill="#147b72" /><Bar dataKey="Type B" stackId="a" fill="#79aaa0" /><Bar dataKey="Type C" stackId="a" fill="#d6ae68" /></BarChart></ResponsiveContainer></div>
      </Panel>
    </div>
    <Panel title="Business line forecast table" subtitle="Scenario-adjusted forecast against illustrative reference plan">
      <div className="table-scroll"><table className="forecast-table"><thead><tr><th>BUSINESS LINE</th><th>STORES</th><th>DEPARTMENTS</th><th>REFERENCE PLAN</th><th>SELECTED FORECAST</th><th>VARIANCE</th><th>MODELLED CONTRIBUTION</th></tr></thead><tbody>{types.map(row => { const variance = row.selected_forecast - row.reference_plan; return <tr key={row.Type}><td><b>Store type {row.Type}</b></td><td>{row.stores}</td><td>{row.departments}</td><td>{money(row.reference_plan, true)}</td><td className="focus-cell">{money(row.selected_forecast, true)}</td><td className={variance >= 0 ? 'positive' : 'negative'}>{variance >= 0 ? '+' : ''}{money(variance, true)}</td><td>{money(row.contribution, true)}</td></tr> })}</tbody></table></div>
      <div className="table-footnote">Store types are anonymised. The modelled contribution is based on the scenario's assumed contribution margin less operating expense rate.</div>
    </Panel>
  </>
}

function ModelPage({ data }) {
  const m = data.metrics
  const audit = data.audit
  return <>
    <div className="page-intro"><div><div className="eyebrow">MODEL GOVERNANCE</div><h2>Model & data quality</h2><p>Review the backtest, data preparation and assumptions behind this planning model.</p></div></div>
    <div className="kpi-grid compact-grid">
      <Metric label="Holiday-weighted MAE" value={money(m.holiday_weighted_mae_usd, true)} note="Holiday observations weighted 5×" icon={Gauge} />
      <Metric label="Weighted MAPE" value={pct(m.holiday_weighted_mape)} note="Weighted absolute error / actuals" icon={Activity} tint="blue" />
      <Metric label="Validation RMSE" value={money(m.rmse_usd, true)} note={`${m.validation_weeks} weekly periods held out`} icon={BarChart3} tint="gold" />
      <Metric label="P90 error band" value={pct(m.backtest_p90_error_band_pct)} note="Indicative range, not probability interval" icon={ShieldCheck} tint="amber" />
    </div>
    <div className="two-column">
      <Panel title="Backtest: actual versus predicted" subtitle={`Recursive holdout from ${m.validation_start}`}>
        <div className="chart-large"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={m.validation_weekly} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}><CartesianGrid vertical={false} stroke="#e9eeee" strokeDasharray="3 5" /><XAxis dataKey="Date" tickFormatter={fmtMonth} axisLine={false} tickLine={false} tick={{ fill: '#75878a', fontSize: 9 }} /><YAxis tickFormatter={v => money(v, true)} axisLine={false} tickLine={false} width={60} tick={{ fill: '#87969a', fontSize: 9 }} /><Tooltip labelFormatter={fmtDate} formatter={v => money(v)} /><Line dataKey="actual" name="Actual sales" stroke="#176c69" strokeWidth={2} dot={false} /><Line dataKey="predicted" name="Model prediction" stroke="#d3a96a" strokeWidth={2} strokeDasharray="5 4" dot={false} /></ComposedChart></ResponsiveContainer></div>
      </Panel>
      <Panel title="Dataset profile" subtitle="Walmart Recruiting Store Sales Forecasting">
        <div className="profile-stat"><span>Historical observations</span><b>{whole(data.metadata.historical_rows)}</b></div>
        <div className="profile-stat"><span>Stores</span><b>{data.metadata.stores}</b></div>
        <div className="profile-stat"><span>Departments</span><b>{data.metadata.departments}</b></div>
        <div className="profile-stat"><span>Historical weeks</span><b>{data.metadata.historical_weeks}</b></div>
        <div className="profile-stat"><span>Forecast horizon</span><b>{data.metadata.forecast_weeks} weeks</b></div>
        <div className="profile-stat"><span>Historical period</span><b>{fmtDate(data.metadata.historical_start)} – {fmtDate(data.metadata.historical_end)}</b></div>
      </Panel>
    </div>
    <Panel title="Data preparation audit" subtitle="Cleaning and join checks performed before modelling">
      <div className="audit-grid">
        <div><span>Duplicate store / department / week rows removed</span><b>{whole(audit.train_cleaning.duplicate_store_dept_week_rows_removed)}</b></div>
        <div><span>Invalid sales rows removed</span><b>{whole(audit.train_cleaning.invalid_sales_rows_removed)}</b></div>
        <div><span>Duplicate store / feature week rows collapsed</span><b>{whole(audit.feature_cleaning.duplicate_store_week_rows_collapsed)}</b></div>
        <div><span>Training rows without matching features</span><b>{whole(audit.train_rows_without_store_week_features)}</b></div>
        <div><span>Missing test feature matches</span><b>{whole(audit.test_rows_without_store_week_features)}</b></div>
        <div><span>Markdown missing values</span><b>Filled with 0</b></div>
      </div>
    </Panel>
    <Panel title="Methodology & limitations" subtitle="What the data can and cannot support">
      <div className="method-list">
        <div><b>Forecast model</b><p>HistGradientBoostingRegressor using store, department and store-type categories; calendar seasonality; holiday flags; regional economic and markdown variables; and backward-looking lag / rolling-sales features. Forecasts are recursive to avoid using future actual sales.</p></div>
        <div><b>Validation</b><p>Time-based holdout of the final 13 available historical weeks (or the available minimum), forecast recursively. Holiday observations receive a 5× weight in weighted MAE, following the competition's emphasis on holiday weeks.</p></div>
        <div><b>Reference plan</b><p>Illustrative seasonal plan: store / department average for the same ISO week across available historical years, multiplied by a 2% planning uplift. This is not an approved corporate budget.</p></div>
        <div><b>Financial assumptions</b><p>The source provides weekly sales but no COGS, payroll, operating expense or cash-flow ledger. Contribution margin and operating expense percentages are editable planning assumptions. Modelled operating contribution is not reported profit, EBITDA or cash flow.</p></div>
        <div><b>Data caveats</b><p>Markdown fields are sparse in the historical dataset and are filled with zero when absent. Macro indicators are forward-filled within store and then median-imputed. The historical data is from 2010–2012 and should not be represented as current Walmart performance.</p></div>
      </div>
    </Panel>
  </>
}

function EmptyState() {
  return <div className="empty-state"><div className="empty-symbol"><FileSpreadsheet size={24} /></div><div className="eyebrow">SOURCE DATA REQUIRED</div><h2>Build your planning workspace</h2><p>Download the Walmart Recruiting Store Sales Forecasting files and place <code>train.csv</code>, <code>test.csv</code>, <code>features.csv</code> and <code>stores.csv</code> in <code>data/raw/</code>. Then run the Python pipeline to generate the dashboard dataset.</p><div className="empty-steps"><div><b>01</b><span>Download the competition data</span><code>Kaggle · Walmart Recruiting</code></div><div><b>02</b><span>Run the modelling pipeline</span><code>python run_analysis.py</code></div><div><b>03</b><span>Launch this Vite application</span><code>cd frontend && npm run dev</code></div></div></div>
}

function downloadCsv(rows) {
  const cols = ['Date', 'revenue', 'reference_plan', 'lower', 'upper']
  const csv = [cols.join(','), ...rows.map(r => cols.map(c => r[c] ?? '').join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'northstar-fpa-forecast.csv'; a.click(); URL.revokeObjectURL(url)
}

export default function App() {
  const [data, setData] = useState(null)
  const [loadStatus, setLoadStatus] = useState('loading')
  const [page, setPage] = useState('overview')
  const [selected, setSelected] = useState('Base case')
  const [assumptions, setAssumptions] = useState({ ...PRESETS['Base case'] })
  const [mobileMenu, setMobileMenu] = useState(false)

  useEffect(() => {
    fetch('/data/financial_plan.json').then(async response => {
      if (!response.ok) throw new Error('Financial planning data is not generated yet.')
      return response.json()
    }).then(json => {
      if (json.status === 'dataset_required' || !json.forecast_weekly?.length) throw new Error('Run the Python analysis pipeline first.')
      setData(json); setLoadStatus('ready')
    }).catch(() => setLoadStatus('empty'))
  }, [])

  useEffect(() => {
    if (!mobileMenu) return undefined
    const closeOnEscape = event => {
      if (event.key === 'Escape') setMobileMenu(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [mobileMenu])

  const derived = useMemo(() => {
    if (!data) return null
    const demand = assumptions.demand_growth_pct / 100
    const priceMix = assumptions.price_mix_pct / 100
    const margin = assumptions.contribution_margin_pct / 100
    const opex = assumptions.operating_expense_pct / 100
    const factor = (1 + demand) * (1 + priceMix)
    const forecast = data.forecast_weekly.map(row => {
      const revenue = Math.max(0, row.model_forecast * factor)
      return { ...row, revenue, lower: revenue * (1 - data.metrics.backtest_p90_error_band_pct), upper: revenue * (1 + data.metrics.backtest_p90_error_band_pct), contribution: revenue * (margin - opex) }
    })
    const forecastRevenue = forecast.reduce((a, r) => a + r.revenue, 0)
    const referencePlan = forecast.reduce((a, r) => a + r.reference_plan, 0)
    const operatingContribution = forecast.reduce((a, r) => a + r.contribution, 0)
    const lower = forecast.reduce((a, r) => a + r.lower, 0)
    const upper = forecast.reduce((a, r) => a + r.upper, 0)
    const planVariance = forecastRevenue - referencePlan
    const chartData = {
      historical_weekly: data.historical_weekly,
      forecast,
      bandPct: data.metrics.backtest_p90_error_band_pct,
    }
    return { forecast, chartData, kpis: { forecastRevenue, referencePlan, operatingContribution, lower, upper, planVariance, planVariancePct: referencePlan ? planVariance / referencePlan : 0 } }
  }, [data, assumptions])

  const pageTitle = NAV.find(n => n.id === page)?.label || 'Revenue forecast'
  if (loadStatus === 'loading') return <div className="loading-screen"><div className="loading-mark">N</div><span>Preparing planning workspace…</span></div>
  if (loadStatus !== 'ready') return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark">N</div><div className="brand-text"><b>northstar</b><small>FINANCIAL PLANNING</small></div></div></aside><main className="main-area"><EmptyState /></main></div>

  return <div className="app-shell">
    {mobileMenu && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMobileMenu(false)} />}
    <aside className={`sidebar ${mobileMenu ? 'mobile-open' : ''}`}>
      <button className="mobile-sidebar-close" aria-label="Close navigation" onClick={() => setMobileMenu(false)}><X size={18} /></button>
      <div className="brand"><div className="brand-mark">N</div><div className="brand-text"><b>northstar</b><small>FINANCIAL PLANNING</small></div><span className="brand-beta">FP&A</span></div>
      <div className="side-divider" />
      <div className="section-caption nav-caption">WORKSPACE</div>
      <nav className="nav-list">{NAV.map(item => { const Icon = item.icon; return <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => { setPage(item.id); setMobileMenu(false) }}><Icon size={17} /><span>{item.label}</span>{page === item.id && <i />}</button> })}</nav>
      <div className="sidebar-divider" />
      <ScenarioSidePanel selected={selected} setSelected={setSelected} assumptions={assumptions} setAssumptions={setAssumptions} metadata={data.metadata} />
      <div className="sidebar-bottom"><div className="side-source"><div className="source-mark"><ShieldCheck size={15} /></div><div><b>Analysis ready</b><small>Reproducible dataset pipeline</small></div></div><div className="sidebar-footer">INDEPENDENT PORTFOLIO PROJECT</div></div>
    </aside>

    <main className="main-area">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu" aria-label="Open navigation" aria-expanded={mobileMenu} onClick={() => setMobileMenu(v => !v)}><Menu size={18} /></button><div className="breadcrumb">Planning workspace <span>/</span> <b>{pageTitle}</b></div></div>
        <div className="topbar-right"><span className="period-pill"><CalendarDays size={13} /> {data.metadata.historical_end.slice(0, 4)} planning horizon</span><span className="source-pill"><i /> WALMART SAMPLE</span><button className="export-button" onClick={() => downloadCsv(derived.forecast)}><Download size={13} /> Export</button></div>
      </header>
      <div className="content">
        <div className="page-title-row"><div><div className="eyebrow">FINANCIAL PLANNING & ANALYSIS</div><h1>{pageTitle === 'Revenue forecast' ? 'Revenue forecast & scenario planning' : pageTitle}</h1><div className="title-tags"><span><i className="live-dot" /> Model generated</span><b>·</b><span>{data.metadata.historical_start} to {data.metadata.historical_end}</span><b>·</b><span>{data.metadata.forecast_weeks}-week forecast</span></div></div><div className="header-selected"><span>ACTIVE SCENARIO</span><b>{selected}</b><ChevronDown size={13} /></div></div>
        {page === 'overview' && <OverviewPage data={data} selected={selected} assumptions={assumptions} derived={derived} setPage={setPage} />}
        {page === 'scenarios' && <ScenarioPage data={data} selected={selected} setSelected={setSelected} assumptions={assumptions} setAssumptions={setAssumptions} derived={derived} />}
        {page === 'segments' && <SegmentPage data={data} assumptions={assumptions} derived={derived} />}
        {page === 'model' && <ModelPage data={data} />}
        <footer className="footer"><span>NORTHSTAR FP&A · INDEPENDENT ANALYTICAL PROJECT</span><span>Source: Walmart Recruiting Store Sales Forecasting · Historical research data only</span></footer>
      </div>
    </main>
  </div>
}
