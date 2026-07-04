"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";

const MARCA = "Vortexia";
const TITULAR = "Tiago Aureliano da Rocha";
const CNPJ = "61.699.939/0001-80";

const inputClass =
  "w-full border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition";

export default function Home() {
  const [form, setForm] = useState({
    nome_ou_razao: "",
    email: "",
    telefone: "",
    mensagem: "",
    website: "",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [erro, setErro] = useState("");

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErro("");

    if (!form.nome_ou_razao.trim() || !form.email.trim() || !form.mensagem.trim()) {
      setErro("Preencha nome ou razão social, e-mail e mensagem.");
      return;
    }

    setStatus("loading");

    try {
      const res = await fetch("/api/qualify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, source: "landing" }),
      });

      const data = await res.json();

      if (!res.ok) {
        setErro(data.error ?? "Erro inesperado. Tente novamente.");
        setStatus("error");
        return;
      }

      setStatus("success");
    } catch {
      setErro("Falha de conexão. Verifique sua internet e tente novamente.");
      setStatus("error");
    }
  }

  return (
    <main className="min-h-screen bg-white flex flex-col">
      <header className="border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <Image
            src="/brand/logo-mark.svg"
            alt=""
            width={32}
            height={32}
            priority
            className="shrink-0"
          />
          <div className="leading-tight">
            <span className="text-sm font-semibold text-gray-900 tracking-wide">{MARCA}</span>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest">
              Inteligência de negócios
            </p>
          </div>
        </div>
      </header>

      <section className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="w-full max-w-lg">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-widest mb-4">
            Inteligência de negócios
          </p>

          <h1 className="text-3xl font-semibold text-gray-900 leading-tight mb-3">
            Descreva o desafio que você ou sua empresa está tentando resolver
          </h1>

          <p className="text-gray-500 text-base mb-10">
            Nossa equipe analisa cada demanda individualmente e entra em contato com as
            possibilidades disponíveis.
          </p>

          {status === "success" ? (
            <div className="rounded-xl border border-gray-100 bg-gray-50 p-8 text-center">
              <p className="text-2xl mb-2" aria-hidden="true">
                ✓
              </p>
              <p className="font-medium text-gray-900 mb-1">Mensagem recebida</p>
              <p className="text-sm text-gray-500">
                Entraremos em contato em até 1 dia útil.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div
                className="absolute opacity-0 pointer-events-none h-0 overflow-hidden"
                aria-hidden="true"
              >
                <label htmlFor="website">Website</label>
                <input
                  id="website"
                  type="text"
                  name="website"
                  value={form.website}
                  onChange={handleChange}
                  tabIndex={-1}
                  autoComplete="off"
                />
              </div>

              <div>
                <label htmlFor="nome_ou_razao" className="block text-sm font-medium text-gray-700 mb-1">
                  Nome ou razão social{" "}
                  <span className="text-gray-400 font-normal">(obrigatório)</span>
                </label>
                <input
                  id="nome_ou_razao"
                  type="text"
                  name="nome_ou_razao"
                  value={form.nome_ou_razao}
                  onChange={handleChange}
                  placeholder="João Silva ou Empresa Exemplo Ltda"
                  className={inputClass}
                  required
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  E-mail{" "}
                  <span className="text-gray-400 font-normal">(obrigatório)</span>
                </label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="contato@email.com"
                  className={inputClass}
                  required
                />
              </div>

              <div>
                <label htmlFor="telefone" className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone{" "}
                  <span className="text-gray-400 font-normal">(opcional)</span>
                </label>
                <input
                  id="telefone"
                  type="tel"
                  name="telefone"
                  value={form.telefone}
                  onChange={handleChange}
                  placeholder="(11) 9 0000-0000"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="mensagem" className="block text-sm font-medium text-gray-700 mb-1">
                  Descreva o desafio{" "}
                  <span className="text-gray-400 font-normal">(obrigatório)</span>
                </label>
                <textarea
                  id="mensagem"
                  name="mensagem"
                  value={form.mensagem}
                  onChange={handleChange}
                  placeholder="Ex.: preciso resolver um problema recorrente com clientes e não sei por onde começar..."
                  rows={5}
                  className={`${inputClass} resize-none`}
                  required
                />
              </div>

              {erro && (
                <p className="text-sm text-red-600" role="alert">
                  {erro}
                </p>
              )}

              <button
                type="submit"
                disabled={status === "loading"}
                className="w-full bg-gray-900 text-white rounded-lg py-3 text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {status === "loading" ? "Enviando..." : "Enviar mensagem"}
              </button>

              <p className="text-xs text-gray-400 text-center">
                Seus dados são tratados conforme a LGPD. Não compartilhamos informações com
                terceiros.
              </p>
            </form>
          )}
        </div>
      </section>

      <footer className="border-t border-gray-100 px-6 py-6 text-center space-y-1">
        <p className="text-xs text-gray-500">
          © {new Date().getFullYear()} {MARCA} · {TITULAR} · CNPJ {CNPJ} · Caraguatatuba/SP
        </p>
        <p className="text-xs text-gray-400">
          Qualificação de demandas comerciais e apoio à prospecção.
        </p>
      </footer>
    </main>
  );
}
