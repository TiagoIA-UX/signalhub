export interface GroqDimensions {
  buying_intent: number;
  urgency: number;
  problem_severity: number;
  niche: "lexrocha" | "zairyx" | "outro";
  intent_summary: string;
  red_flags: string[];
}

const WEIGHTS = {
  buying_intent: 0.4,
  urgency: 0.35,
  problem_severity: 0.25,
} as const;

const RED_FLAG_PATTERN =
  /advogado|advogada|processo aberto|só pesquisando|apenas curiosidade|sem orçamento/i;

function clamp(n: number): number {
  return Math.max(0, Math.min(100, Math.round(n)));
}

export function computeFinalScore(dims: GroqDimensions): number {
  let score =
    clamp(dims.buying_intent) * WEIGHTS.buying_intent +
    clamp(dims.urgency) * WEIGHTS.urgency +
    clamp(dims.problem_severity) * WEIGHTS.problem_severity;

  if (dims.red_flags?.some((f) => RED_FLAG_PATTERN.test(f))) {
    score *= 0.7;
  }

  return Math.round(score);
}

export const SCORE_WEIGHTS = WEIGHTS;

export function normalizeDimensions(raw: Partial<GroqDimensions>): GroqDimensions {
  const niche =
    raw.niche === "lexrocha" || raw.niche === "zairyx" || raw.niche === "outro"
      ? raw.niche
      : "outro";

  return {
    buying_intent: clamp(Number(raw.buying_intent) || 50),
    urgency: clamp(Number(raw.urgency) || 50),
    problem_severity: clamp(Number(raw.problem_severity) || 50),
    niche,
    intent_summary: String(raw.intent_summary ?? "").slice(0, 120) || "Demanda a classificar",
    red_flags: Array.isArray(raw.red_flags) ? raw.red_flags.map(String) : [],
  };
}
