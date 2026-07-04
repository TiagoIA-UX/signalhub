import { NextResponse } from "next/server";
import { getGroq } from "@/lib/groq";
import { getSupabase } from "@/lib/supabase";
import {
  computeFinalScore,
  normalizeDimensions,
  SCORE_WEIGHTS,
  type GroqDimensions,
} from "@/lib/score";

const GROQ_SYSTEM = `Você qualifica demandas comerciais brasileiras para apoio à prospecção.
Retorne SOMENTE JSON válido, sem markdown.

{
  "buying_intent": 0-100,
  "urgency": 0-100,
  "problem_severity": 0-100,
  "niche": "lexrocha" | "zairyx" | "outro",
  "intent_summary": "frase única até 120 caracteres",
  "red_flags": []
}

Regras:
- buying_intent >= 70 SOMENTE se há intenção real de contratar ou resolver pagando
- urgency = urgência declarada ou implícita
- problem_severity = gravidade do PROBLEMA, não capacidade financeira da pessoa
- niche: lexrocha = CDC/consumidor; zairyx = delivery/restaurante; outro = demais
- red_flags: ex. ["já tem advogado", "só pesquisando"]
- NUNCA inferir financial_capacity — não existe neste schema
- Sem informação suficiente → pontue 50`;

type LeadInput = {
  nome_ou_razao: string;
  email: string;
  telefone?: string;
  mensagem: string;
  source?: string;
  website?: string;
};

function groqFallback(): GroqDimensions {
  return {
    buying_intent: 50,
    urgency: 50,
    problem_severity: 50,
    niche: "outro",
    intent_summary: "Erro na classificação — revisar manualmente",
    red_flags: ["groq_error"],
  };
}

export async function POST(req: Request) {
  let body: LeadInput;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "JSON inválido" }, { status: 400 });
  }

  if (body.website?.trim()) {
    return NextResponse.json({ ok: true, mensagem: "Recebemos sua mensagem." });
  }

  const { nome_ou_razao, email, mensagem, telefone, source } = body;

  if (!nome_ou_razao?.trim() || !email?.trim() || !mensagem?.trim()) {
    return NextResponse.json(
      { error: "nome_ou_razao, email e mensagem são obrigatórios" },
      { status: 400 }
    );
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "E-mail inválido" }, { status: 400 });
  }

  let dims: GroqDimensions;
  try {
    if (!process.env.GROQ_API_KEY) {
      throw new Error("GROQ_API_KEY ausente");
    }

    const completion = await getGroq().chat.completions.create({
      model: "openai/gpt-oss-120b",
      max_tokens: 300,
      temperature: 0.1,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: GROQ_SYSTEM },
        {
          role: "user",
          content: [
            `Nome ou razão social: ${nome_ou_razao}`,
            `E-mail: ${email}`,
            telefone ? `Telefone: ${telefone}` : null,
            `Mensagem: ${mensagem}`,
          ]
            .filter(Boolean)
            .join("\n"),
        },
      ],
    });

    const raw = JSON.parse(completion.choices[0].message.content ?? "{}");
    dims = normalizeDimensions(raw);
  } catch (err) {
    console.error("[qualify] Groq erro:", err);
    dims = groqFallback();
  }

  const final_score = computeFinalScore(dims);

  let lead: { id: string; final_score: number; niche: string; intent_summary: string };
  try {
    const supabase = getSupabase();
    const { data, error: dbError } = await supabase
      .from("leads")
      .insert({
        nome_ou_razao,
        email,
        telefone: telefone ?? null,
        mensagem,
        source: source ?? "landing",
        niche: dims.niche,
        buying_intent: dims.buying_intent,
        urgency_score: dims.urgency,
        problem_severity: dims.problem_severity,
        intent_summary: dims.intent_summary,
        red_flags: dims.red_flags,
        final_score,
        score_weights: SCORE_WEIGHTS,
        status: "novo",
        telegram_sent: false,
      })
      .select("id, final_score, niche, intent_summary")
      .single();

    if (dbError || !data) {
      console.error("[qualify] Supabase erro:", dbError);
      return NextResponse.json({ error: "Erro ao salvar lead" }, { status: 500 });
    }
    lead = data;
  } catch (err) {
    console.error("[qualify] Supabase config:", err);
    return NextResponse.json({ error: "Erro ao salvar lead" }, { status: 500 });
  }

  const urgenciaLabel =
    dims.urgency >= 80 ? "Alta" : dims.urgency >= 60 ? "Média" : "Baixa";
  const nicheLabel = { lexrocha: "CDC", zairyx: "Delivery", outro: "Outro" }[dims.niche];
  const flagsTexto =
    dims.red_flags.length > 0 ? `Red flags: ${dims.red_flags.join(", ")}` : "";

  const mensagemTelegram = [
    `Lead: ${nome_ou_razao}`,
    `Score: ${final_score}/100 | ${nicheLabel} | Urgência: ${urgenciaLabel}`,
    `${email}${telefone ? ` | ${telefone}` : ""}`,
    "",
    dims.intent_summary,
    flagsTexto,
    "",
    "Mensagem:",
    mensagem.slice(0, 300) + (mensagem.length > 300 ? "..." : ""),
    "",
    `ID: ${lead.id}`,
  ]
    .filter(Boolean)
    .join("\n");

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (token && chatId) {
    try {
      const tgRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text: mensagemTelegram,
          disable_web_page_preview: true,
        }),
      });
      if (tgRes.ok) {
        const supabase = getSupabase();
        await supabase.from("leads").update({ telegram_sent: true }).eq("id", lead.id);
      }
    } catch (err) {
      console.error("[qualify] Telegram erro:", err);
    }
  }

  return NextResponse.json({
    ok: true,
    leadId: lead.id,
    mensagem: "Recebemos sua mensagem. Em breve entraremos em contato.",
  });
}
