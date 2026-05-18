import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { Calculator as CalcIcon, Play, RefreshCw, ToggleLeft, ToggleRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { calculate, METHODOLOGY_LABELS, METHODOLOGIES, type Methodology, type CalcResult, type CalcRequest } from "@/lib/api";
type Mode = "standard" | "comparison";

interface FormValues {
  fNRB: number;
  numHouseholds: number;
  householdSize: number;
  baselineConsumption: number;
  projectConsumption: number;
  leakageDiscount: number;
  usageRate: number;
  DAF: number;
  baselineFuel: string;
  projectFuel: string;
}

const DEFAULTS: FormValues = {
  fNRB: 0.75,
  numHouseholds: 5000,
  householdSize: 5,
  baselineConsumption: 2.0,
  projectConsumption: 0.8,
  leakageDiscount: 0.95,
  usageRate: 0.90,
  DAF: 0.025,
  baselineFuel: "wood",
  projectFuel: "wood",
};

const COMP_COLORS: Record<Methodology, string> = {
  RECH: "#00C896",
  TPDDTEC: "#60a5fa",
  VM0050: "#f59e0b",
  MECD: "#a78bfa",
};

function buildParams(methodology: Methodology, form: FormValues): Record<string, unknown> {
  const base = { fNRB: form.fNRB };
  switch (methodology) {
    case "RECH":
      return {
        ...base,
        N_distributed: form.numHouseholds,
        baseline_consumption: form.baselineConsumption,
        project_consumption: form.projectConsumption,
        HNb: form.householdSize,
        DAF: form.DAF,
        baseline_fuel: form.baselineFuel,
        project_fuel: form.projectFuel,
      };
    case "TPDDTEC":
      return {
        ...base,
        num_households: form.numHouseholds,
        household_size: form.householdSize,
        baseline_fuel_consumption: form.baselineConsumption,
        project_fuel_consumption: form.projectConsumption,
        leakage_discount: form.leakageDiscount,
        usage_rate: form.usageRate,
        baseline_fuel: form.baselineFuel,
        project_fuel: form.projectFuel,
      };
    case "VM0050":
      return {
        ...base,
        num_households: form.numHouseholds,
        household_size: form.householdSize,
        baseline_fuel_consumption: form.baselineConsumption,
        project_fuel_consumption: form.projectConsumption,
        leakage_discount: form.leakageDiscount,
        usage_rate: form.usageRate,
      };
    case "MECD":
      return {
        ...base,
        N_households: form.numHouseholds,
        household_size: form.householdSize,
      };
  }
}

function NumInput({
  label, id, value, onChange, step = 0.01, min, max, unit,
}: {
  label: string; id: string; value: number; onChange: (v: number) => void;
  step?: number; min?: number; max?: number; unit?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-xs text-muted-foreground font-medium">
        {label}{unit && <span className="ml-1 text-muted-foreground/60">({unit})</span>}
      </Label>
      <Input
        id={id}
        data-testid={`input-${id}`}
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="bg-input border-border h-8 text-sm"
      />
    </div>
  );
}

function FuelSelect({ id, label, value, onChange }: {
  id: string; label: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground font-medium">{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger data-testid={`select-${id}`} className="bg-input border-border h-8 text-sm">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="wood">Bois</SelectItem>
          <SelectItem value="charcoal">Charbon</SelectItem>
          <SelectItem value="lpg">GPL</SelectItem>
          <SelectItem value="biogas">Biogaz</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

function ResultsSingle({ result, methodology }: { result: CalcResult; methodology: Methodology }) {
  const chartData = (result.years || result.year_by_year || []).map((y) => ({
    year: `An ${y.year_number}`,
    "ER net": Math.round(y.net_er ?? 0),
    "BE": Math.round(y.baseline_emissions ?? 0),
  }));

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total credits", value: result.summary?.total_er?.toLocaleString("fr-FR", { maximumFractionDigits: 0 }), unit: "tCO2e" },
          { label: "Moy. annuelle", value: result.summary?.average_annual_er?.toLocaleString("fr-FR", { maximumFractionDigits: 0 }), unit: "tCO2e/an" },
          { label: "Duree", value: result.summary?.crediting_years, unit: "ans" },
        ].map(({ label, value, unit }) => (
          <Card key={label} className="bg-card border-card-border">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
              <p className="text-2xl font-bold mt-1" data-testid={`text-result-${label}`}>
                {value} <span className="text-sm font-normal text-muted-foreground">{unit}</span>
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {result.warnings?.length > 0 && (
        <div className="rounded-md bg-yellow-500/10 border border-yellow-500/20 px-4 py-3 text-sm text-yellow-300 space-y-1">
          {result.warnings.map((w, i) => <p key={i}>{w}</p>)}
        </div>
      )}

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Evolution annuelle — ER net (tCO2e)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(228 20% 18%)" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: "hsl(214 15% 55%)" }} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(214 15% 55%)" }} />
              <Tooltip
                contentStyle={{ background: "hsl(228 23% 12%)", border: "1px solid hsl(228 20% 18%)", borderRadius: 6 }}
                labelStyle={{ color: "hsl(214 32% 91%)" }}
              />
              <Bar dataKey="ER net" fill={COMP_COLORS[methodology]} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Detail annee par annee</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground uppercase">
                <th className="text-left px-4 py-2">Annee</th>
                <th className="text-right px-4 py-2">Calendrier</th>
                <th className="text-right px-4 py-2">BE (tCO2e)</th>
                <th className="text-right px-4 py-2">PE (tCO2e)</th>
                <th className="text-right px-4 py-2">ER brut</th>
                <th className="text-right px-4 py-2">ER net</th>
              </tr>
            </thead>
            <tbody>
              {(result.years || result.year_by_year || []).map((y) => (
                <tr key={y.year_number} className="border-b border-border/50 hover:bg-accent/30">
                  <td className="px-4 py-2 font-medium">{y.year_number}</td>
                  <td className="px-4 py-2 text-right text-muted-foreground">{y.calendar_year}</td>
                  <td className="px-4 py-2 text-right">{(y.baseline_emissions ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}</td>
                  <td className="px-4 py-2 text-right">{(y.project_emissions ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}</td>
                  <td className="px-4 py-2 text-right">{((y.gross_er ?? y.net_er) ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}</td>
                  <td className="px-4 py-2 text-right font-semibold text-primary">{(y.net_er ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function ResultsComparison({ results }: { results: Record<string, CalcResult | undefined> }) {
  const methodologies = METHODOLOGIES.filter((m) => !!results[m]);
  if (!methodologies.length) return null;

  const firstResult = results[methodologies[0]]!;
  const years = firstResult.years || firstResult.year_by_year || [];

  const chartData = years.map((y) => {
    const row: Record<string, number | string> = { year: `An ${y.year_number}` };
    methodologies.forEach((m) => {
      const r = results[m];
      const yr = (r?.years || r?.year_by_year || [])[y.year_number - 1];
      row[METHODOLOGY_LABELS[m]] = Math.round(yr?.net_er ?? 0);
    });
    return row;
  });

  const best = methodologies.reduce((a, b) =>
    (results[a]?.summary?.total_er ?? 0) > (results[b]?.summary?.total_er ?? 0) ? a : b
  );

  return (
    <div className="space-y-5">
      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Comparaison des methodologies</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground uppercase">
                <th className="text-left px-4 py-2">Methodologie</th>
                <th className="text-right px-4 py-2">Total (tCO2e)</th>
                <th className="text-right px-4 py-2">Moy./an (tCO2e)</th>
                <th className="text-right px-4 py-2">An 1 (tCO2e)</th>
              </tr>
            </thead>
            <tbody>
              {methodologies.map((m) => {
                const r = results[m]!;
                const yr1 = (r.years || r.year_by_year || [])[0];
                const isBest = m === best;
                return (
                  <tr key={m} className={`border-b border-border/50 ${isBest ? "bg-primary/5" : "hover:bg-accent/30"}`}>
                    <td className="px-4 py-2 font-medium flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: COMP_COLORS[m] }} />
                      {METHODOLOGY_LABELS[m]}
                      {isBest && <span className="ml-1 text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-semibold">FAVORABLE</span>}
                    </td>
                    <td className="px-4 py-2 text-right font-semibold">{(r.summary?.total_er ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 })}</td>
                    <td className="px-4 py-2 text-right">{(r.summary?.average_annual_er ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 })}</td>
                    <td className="px-4 py-2 text-right">{((yr1?.net_er) ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 })}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card className="bg-card border-card-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">ER net annuel par methodologie (tCO2e)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(228 20% 18%)" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: "hsl(214 15% 55%)" }} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(214 15% 55%)" }} />
              <Tooltip
                contentStyle={{ background: "hsl(228 23% 12%)", border: "1px solid hsl(228 20% 18%)", borderRadius: 6 }}
                labelStyle={{ color: "hsl(214 32% 91%)" }}
              />
              <Legend wrapperStyle={{ fontSize: 11, color: "hsl(214 15% 55%)" }} />
              {methodologies.map((m) => (
                <Bar key={m} dataKey={METHODOLOGY_LABELS[m]} fill={COMP_COLORS[m]} radius={[2, 2, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Calculator() {
  const [mode, setMode] = useState<Mode>("standard");
  const [methodology, setMethodology] = useState<Methodology>("RECH");
  const [creditingYears, setCreditingYears] = useState(5);
  const [form, setForm] = useState<FormValues>(DEFAULTS);
  const [result, setResult] = useState<CalcResult | null>(null);
  const [compResults, setCompResults] = useState<Partial<Record<Methodology, CalcResult>>>({});

  function setField<K extends keyof FormValues>(k: K, v: FormValues[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  const calcMutation = useMutation({
    mutationFn: (req: CalcRequest) => calculate(req),
  });

  async function handleCalculate() {
    setResult(null);
    setCompResults({});
    const startYear = new Date().getFullYear();

    if (mode === "standard") {
      const res = await calcMutation.mutateAsync({
        methodology,
        params: buildParams(methodology, form),
        crediting_years: creditingYears,
        start_year: startYear,
      });
      setResult(res);
    } else {
      const results: Partial<Record<Methodology, CalcResult>> = {};
      await Promise.allSettled(
        METHODOLOGIES.map(async (m) => {
          try {
            const res = await calculate({
              methodology: m,
              params: buildParams(m, form),
              crediting_years: creditingYears,
              start_year: startYear,
            });
            results[m] = res;
          } catch {
            /* skip failed methodologies gracefully */
          }
        })
      );
      setCompResults(results);
    }
  }

  const isLoading = calcMutation.isPending;
  const isComparison = mode !== "standard";

  const showRECH = isComparison || methodology === "RECH";
  const showTPDDTEC = isComparison || methodology === "TPDDTEC";
  const showVM0050 = isComparison || methodology === "VM0050";
  const showLeakage = showTPDDTEC || showVM0050;
  const showFuel = isComparison || showRECH || showTPDDTEC;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CalcIcon className="w-6 h-6 text-primary" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Calculateur ER</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Simulation des reductions d'emissions</p>
          </div>
        </div>

        <button
          data-testid="toggle-mode"
          onClick={() => { setMode(mode === "standard" ? "comparison" : "standard"); setResult(null); setCompResults({}); }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border text-sm text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
        >
          {!isComparison ? <ToggleLeft className="w-4 h-4" /> : <ToggleRight className="w-4 h-4 text-primary" />}
          {!isComparison ? "Mode standard" : "Mode comparaison"}
        </button>
      </div>

      <div className="grid grid-cols-[300px_1fr] gap-6 items-start">
        <Card className="bg-card border-card-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Parametres</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!isComparison && (
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground font-medium">Methodologie</Label>
                <Select value={methodology} onValueChange={(v) => { setMethodology(v as Methodology); setResult(null); }}>
                  <SelectTrigger data-testid="select-methodology" className="bg-input border-border h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {METHODOLOGIES.map((m) => (
                      <SelectItem key={m} value={m}>{METHODOLOGY_LABELS[m]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground font-medium">
                Duree de creditisation : <span className="text-foreground font-semibold">{creditingYears} ans</span>
              </Label>
              <Slider
                data-testid="slider-crediting-years"
                min={1} max={10} step={1}
                value={[creditingYears]}
                onValueChange={([v]) => setCreditingYears(v)}
                className="mt-2"
              />
            </div>

            <div className="border-t border-border pt-3 space-y-3">
              <p className="text-[11px] text-muted-foreground font-semibold uppercase tracking-wider">Communs</p>
              <NumInput label="fNRB" id="fNRB" value={form.fNRB} onChange={(v) => setField("fNRB", v)} min={0} max={1} step={0.01} />
              <NumInput label="Menages / Appareils" id="numHouseholds" value={form.numHouseholds} onChange={(v) => setField("numHouseholds", v)} step={100} min={1} />
              <NumInput label="Taille menage" id="householdSize" value={form.householdSize} onChange={(v) => setField("householdSize", v)} step={0.5} min={1} unit="pers/mge" />
              <NumInput label="Conso. baseline" id="baselineConsumption" value={form.baselineConsumption} onChange={(v) => setField("baselineConsumption", v)} step={0.1} min={0.01} unit="t/app/an" />
              <NumInput label="Conso. projet" id="projectConsumption" value={form.projectConsumption} onChange={(v) => setField("projectConsumption", v)} step={0.1} min={0.001} unit="t/app/an" />
            </div>

            {showLeakage && (
              <div className="border-t border-border pt-3 space-y-3">
                <p className="text-[11px] text-muted-foreground font-semibold uppercase tracking-wider">TPDDTEC / VM0050</p>
                <NumInput label="Discount fuites (0-1)" id="leakageDiscount" value={form.leakageDiscount} onChange={(v) => setField("leakageDiscount", v)} step={0.01} min={0} max={1} />
                <NumInput label="Taux utilisation" id="usageRate" value={form.usageRate} onChange={(v) => setField("usageRate", v)} step={0.01} min={0} max={1} />
              </div>
            )}

            {showFuel && (
              <div className="border-t border-border pt-3 space-y-3">
                <p className="text-[11px] text-muted-foreground font-semibold uppercase tracking-wider">Combustibles</p>
                <FuelSelect id="baselineFuel" label="Combustible baseline" value={form.baselineFuel} onChange={(v) => setField("baselineFuel", v)} />
                <FuelSelect id="projectFuel" label="Combustible projet" value={form.projectFuel} onChange={(v) => setField("projectFuel", v)} />
              </div>
            )}

            {(showRECH || isComparison) && (
              <div className="border-t border-border pt-3 space-y-3">
                <p className="text-[11px] text-muted-foreground font-semibold uppercase tracking-wider">RECH</p>
                <NumInput label="DAF (facteur ajustement)" id="DAF" value={form.DAF} onChange={(v) => setField("DAF", v)} step={0.001} min={0} max={0.1} />
              </div>
            )}

            <Button
              data-testid="button-calculate"
              onClick={handleCalculate}
              disabled={isLoading}
              className="w-full gap-2 mt-2"
            >
              {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {isLoading ? "Calcul en cours..." : "Lancer le calcul"}
            </Button>

            {calcMutation.isError && (
              <p className="text-xs text-destructive mt-1">{String(calcMutation.error)}</p>
            )}
          </CardContent>
        </Card>

        <div className="min-h-[200px]">
          {!result && !Object.keys(compResults).length && !isLoading && (
            <div className="flex flex-col items-center justify-center h-64 text-center text-muted-foreground border border-dashed border-border rounded-lg">
              <CalcIcon className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm">Configurez les parametres et lancez le calcul.</p>
              <p className="text-xs mt-1">
                {isComparison ? "Les 4 methodologies seront comparees simultanement." : `Methodologie : ${METHODOLOGY_LABELS[methodology]}`}
              </p>
            </div>
          )}
          {isLoading && (
            <div className="flex items-center justify-center h-64 text-muted-foreground text-sm gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-primary" />
              Calcul en cours{isComparison ? " (4 methodologies)..." : "..."}
            </div>
          )}
          {!isComparison && result && <ResultsSingle result={result} methodology={methodology} />}
          {isComparison && Object.keys(compResults).length > 0 && <ResultsComparison results={compResults} />}
        </div>
      </div>
    </div>
  );
}
