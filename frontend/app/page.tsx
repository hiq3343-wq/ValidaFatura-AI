"use client";

import {
  BrainCircuit,
  CheckCircle2,
  CircleAlert,
  FileCheck2,
  FileText,
  LoaderCircle,
  ReceiptText,
  ScanText,
  SearchCheck,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import type {
  ChangeEvent,
  FormEvent,
  ReactNode,
} from "react";


type Transacao = {
  empresa: string;
  valor: number;
  data: string | null;
  parcela_atual?: number | null;
  total_parcelas?: number | null;
};


type Comparacao = {
  empresa: string;
  empresa_fatura?: string;
  recibo?: number | null;
  fatura?: number | null;
  data_recibo?: string;
  data_fatura?: string;
  status: string;
};


type ResultadoValidacao = {
  transacoes_fatura: Transacao[];
  transacoes_recibos: Transacao[];
  comparacao: Comparacao[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";
const ETAPAS_CARREGAMENTO = [
  {
    titulo: "Enviando documentos",
    descricao: "Preparando os arquivos para análise.",
    icone: UploadCloud,
  },
  {
    titulo: "Extraindo os textos",
    descricao: "O OCR está lendo a fatura e os comprovantes.",
    icone: ScanText,
  },
  {
    titulo: "Analisando com IA",
    descricao: "Identificando empresas, valores, datas e parcelas.",
    icone: BrainCircuit,
  },
  {
    titulo: "Comparando transações",
    descricao: "Conferindo os comprovantes com os lançamentos.",
    icone: SearchCheck,
  },
];


export default function Home() {
  const [fatura, setFatura] = useState<File | null>(null);
  const [recibos, setRecibos] = useState<File[]>([]);

  const [resultado, setResultado] =
    useState<ResultadoValidacao | null>(null);

  const [carregando, setCarregando] = useState(false);
  const [etapaAtual, setEtapaAtual] = useState(0);
  const [erro, setErro] = useState("");


  useEffect(() => {
    if (!carregando) {
      setEtapaAtual(0);
      return;
    }

    const intervalo = window.setInterval(() => {
      setEtapaAtual((etapaAnterior) =>
        Math.min(
          etapaAnterior + 1,
          ETAPAS_CARREGAMENTO.length - 1
        )
      );
    }, 2500);

    return () => window.clearInterval(intervalo);
  }, [carregando]);


  function selecionarFatura(
    evento: ChangeEvent<HTMLInputElement>
  ) {
    const arquivo = evento.target.files?.[0] ?? null;

    setFatura(arquivo);
    setResultado(null);
    setErro("");
  }


  function selecionarRecibos(
    evento: ChangeEvent<HTMLInputElement>
  ) {
    const arquivos = Array.from(
      evento.target.files ?? []
    );

    setRecibos(arquivos);
    setResultado(null);
    setErro("");
  }


  async function validarDocumentos(
    evento: FormEvent<HTMLFormElement>
  ) {
    evento.preventDefault();

    if (!fatura) {
      setErro("Selecione uma fatura de cartão em PDF.");
      return;
    }

    if (recibos.length === 0) {
      setErro(
        "Selecione pelo menos um recibo ou comprovante."
      );
      return;
    }

    const formulario = new FormData();

    formulario.append("fatura", fatura);

    recibos.forEach((recibo) => {
      formulario.append("recibos", recibo);
    });

    try {
      setCarregando(true);
      setEtapaAtual(0);
      setErro("");
      setResultado(null);

      const resposta = await fetch(
  `${API_URL}/validar`,
        {
          method: "POST",
          body: formulario,
        }
      );

      const dados = await resposta.json();

      if (!resposta.ok) {
        throw new Error(
          dados.detail ??
            "Não foi possível validar os documentos."
        );
      }

      setResultado(dados);
    } catch (erroDesconhecido) {
      const mensagem =
        erroDesconhecido instanceof Error
          ? erroDesconhecido.message
          : "Ocorreu um erro inesperado.";

      setErro(mensagem);
    } finally {
      setCarregando(false);
    }
  }


  function formatarValor(
    valor?: number | null
  ) {
    if (valor === undefined || valor === null) {
      return "—";
    }

    return valor.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }


  function configurarStatus(status: string) {
    if (status === "CONFIRMADO") {
      return {
        texto: "Confirmado",
        classes:
          "border-emerald-200 bg-emerald-100 text-emerald-800",
        icone: CheckCircle2,
      };
    }

    if (status === "CONFIRMADO - PARCELADO") {
      return {
        texto: "Confirmado · Parcelado",
        classes:
          "border-blue-200 bg-blue-100 text-blue-800",
        icone: FileCheck2,
      };
    }

    if (status.includes("DIFERENTE")) {
      return {
        texto:
          status === "DATA DIFERENTE"
            ? "Data divergente"
            : "Valor divergente",
        classes:
          "border-amber-200 bg-amber-100 text-amber-800",
        icone: CircleAlert,
      };
    }
        if (status === "SEM COMPROVANTE") {
      return {
        texto: "Sem comprovante",
        classes:
          "border-red-200 bg-red-100 text-red-800",
        icone: CircleAlert,
      };
    }

    return {
      texto: "Não encontrado",
      classes:
        "border-red-200 bg-red-100 text-red-800",
      icone: CircleAlert,
    };
  }


  const totalConfirmados = useMemo(() => {
    return (
      resultado?.comparacao.filter((item) =>
        item.status.startsWith("CONFIRMADO")
      ).length ?? 0
    );
  }, [resultado]);


  const totalDivergencias = useMemo(() => {
    return (
      resultado?.comparacao.filter(
        (item) =>
          !item.status.startsWith("CONFIRMADO")
      ).length ?? 0
    );
  }, [resultado]);


  const percentualConfirmado = useMemo(() => {
    if (
      !resultado ||
      resultado.comparacao.length === 0
    ) {
      return 0;
    }

    return Math.round(
      (
        totalConfirmados /
        resultado.comparacao.length
      ) * 100
    );
  }, [resultado, totalConfirmados]);


  const etapa = ETAPAS_CARREGAMENTO[etapaAtual];
  const IconeEtapa = etapa.icone;


  return (
    <main className="min-h-screen bg-slate-950 text-slate-900">
      <header className="border-b border-white/10 bg-slate-950">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-5 sm:px-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-950/40">
            <ReceiptText size={24} />
          </div>

          <div>
            <p className="text-lg font-bold text-white">
              ValidaFatura AI
            </p>

            <p className="text-sm text-slate-400">
              Sistema inteligente de conferência de comprovantes
            </p>
          </div>
        </div>
      </header>


      <section className="bg-gradient-to-b from-slate-950 via-slate-900 to-slate-100 px-4 pb-20 pt-14 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-4xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-400/10 px-3 py-1 text-sm font-medium text-blue-300">
              <BrainCircuit size={16} />
              Powered by OCR + IA
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              Confira faturas e comprovantes em poucos segundos
            </h1>

            <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300 sm:text-lg">
              Envie uma fatura e os comprovantes das compras.
              O sistema utiliza OCR e Inteligência Artificial
              para identificar automaticamente as transações,
              reconhecer parcelamentos e destacar divergências.
            </p>
          </div>


          <form
            onSubmit={validarDocumentos}
            className="mt-10 rounded-3xl border border-white/10 bg-white p-5 shadow-2xl shadow-slate-950/30 sm:p-8"
          >
            <div className="grid gap-6 lg:grid-cols-2">
              <label className="group block rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-5 transition hover:border-blue-400 hover:bg-blue-50/40">
                <div className="mb-5 flex items-start gap-3">
                  <div className="rounded-xl bg-blue-100 p-3 text-blue-700">
                    <FileText size={23} />
                  </div>

                  <div>
                    <p className="font-bold text-slate-900">
                      Fatura do cartão
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      Selecione um arquivo PDF com os lançamentos.
                    </p>
                  </div>
                </div>

                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={selecionarFatura}
                  className="block w-full cursor-pointer rounded-xl border border-slate-200 bg-white p-2 text-sm file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-blue-600 file:px-4 file:py-2.5 file:font-semibold file:text-white hover:file:bg-blue-700"
                />

                {fatura && (
                  <div className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    <CheckCircle2 size={17} />

                    <span className="truncate">
                      {fatura.name}
                    </span>
                  </div>
                )}
              </label>


              <label className="group block rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-5 transition hover:border-violet-400 hover:bg-violet-50/40">
                <div className="mb-5 flex items-start gap-3">
                  <div className="rounded-xl bg-violet-100 p-3 text-violet-700">
                    <ReceiptText size={23} />
                  </div>

                  <div>
                    <p className="font-bold text-slate-900">
                      Recibos e comprovantes
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      Selecione várias imagens ou arquivos PDF.
                    </p>
                  </div>
                </div>

                <input
                  type="file"
                  multiple
                  accept=".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
                  onChange={selecionarRecibos}
                  className="block w-full cursor-pointer rounded-xl border border-slate-200 bg-white p-2 text-sm file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-violet-600 file:px-4 file:py-2.5 file:font-semibold file:text-white hover:file:bg-violet-700"
                />

                {recibos.length > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-violet-800">
                      <CheckCircle2 size={17} />

                      {recibos.length} arquivo(s) selecionado(s)
                    </div>

                    <ul className="mt-3 max-h-28 space-y-1 overflow-y-auto rounded-lg bg-white p-3 text-xs text-slate-500">
                      {recibos.map((arquivo) => (
                        <li
                          key={`${arquivo.name}-${arquivo.size}`}
                          className="truncate"
                        >
                          {arquivo.name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </label>
            </div>


            {erro && (
              <div className="mt-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <CircleAlert
                  size={20}
                  className="mt-0.5 shrink-0"
                />

                <span>{erro}</span>
              </div>
            )}


            {carregando && (
              <div className="mt-6 rounded-2xl border border-blue-100 bg-blue-50 p-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
                    <IconeEtapa size={23} />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-bold text-blue-950">
                        {etapa.titulo}
                      </p>

                      <LoaderCircle
                        size={17}
                        className="animate-spin text-blue-600"
                      />
                    </div>

                    <p className="mt-1 text-sm text-blue-800/70">
                      {etapa.descricao}
                    </p>
                  </div>
                </div>

                <div className="mt-5 h-2 overflow-hidden rounded-full bg-blue-100">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all duration-700"
                    style={{
                      width: `${
                        (
                          (etapaAtual + 1) /
                          ETAPAS_CARREGAMENTO.length
                        ) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            )}


            <button
              type="submit"
              disabled={carregando}
              className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 font-bold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
            >
              {carregando ? (
                <>
                  <LoaderCircle
                    size={19}
                    className="animate-spin"
                  />
                  Validando documentos
                </>
              ) : (
                <>
                  <ShieldCheck size={19} />
                  Validar documentos
                </>
              )}
            </button>
          </form>
        </div>
      </section>


      {resultado && (
        <section className="-mt-10 bg-slate-100 px-4 pb-16 sm:px-6">
          <div className="mx-auto max-w-7xl">
            <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <ResumoCard
                titulo="Compras na fatura"
                valor={resultado.transacoes_fatura.length}
                descricao="Lançamentos identificados"
                classes="border-blue-200 bg-blue-50 text-blue-800"
                icone={<FileText size={22} />}
              />

              <ResumoCard
                titulo="Comprovantes"
                valor={resultado.transacoes_recibos.length}
                descricao="Documentos processados"
                classes="border-violet-200 bg-violet-50 text-violet-800"
                icone={<ReceiptText size={22} />}
              />

              <ResumoCard
                titulo="Confirmados"
                valor={totalConfirmados}
                descricao="Transações correspondentes"
                classes="border-emerald-200 bg-emerald-50 text-emerald-800"
                icone={<CheckCircle2 size={22} />}
              />

              <ResumoCard
                titulo="Divergências"
                valor={totalDivergencias}
                descricao="Itens que precisam de revisão"
                classes="border-red-200 bg-red-50 text-red-800"
                icone={<CircleAlert size={22} />}
              />
            </div>


            <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm font-semibold text-slate-500">
                    Taxa de conferência
                  </p>

                  <p className="mt-1 text-2xl font-bold">
                    {percentualConfirmado}% confirmado
                  </p>
                </div>

                <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
                  <ShieldCheck size={19} />

                  {totalConfirmados} de{" "}
                  {resultado.comparacao.length} comprovantes
                </div>
              </div>

              <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-1000"
                  style={{
                    width: `${percentualConfirmado}%`,
                  }}
                />
              </div>
            </div>


            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center gap-3 border-b border-slate-200 px-6 py-5">
                <div className="rounded-lg bg-slate-100 p-2 text-slate-700">
                  <SearchCheck size={21} />
                </div>

                <div>
                  <h2 className="text-lg font-bold">
                    Resultado da comparação
                  </h2>

                  <p className="text-sm text-slate-500">
                    Conferência entre comprovantes e lançamentos
                    da fatura.
                  </p>
                </div>
              </div>


              <div className="hidden overflow-x-auto md:block">
                <table className="w-full min-w-[950px] text-left">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-6 py-4 font-semibold">
                        Comprovante
                      </th>

                      <th className="px-6 py-4 font-semibold">
                        Lançamento
                      </th>

                      <th className="px-6 py-4 font-semibold">
                        Recibo
                      </th>

                      <th className="px-6 py-4 font-semibold">
                        Fatura
                      </th>

                      <th className="px-6 py-4 font-semibold">
                        Datas
                      </th>

                      <th className="px-6 py-4 font-semibold">
                        Status
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-100">
                    {resultado.comparacao.map(
                      (item, indice) => {
                        const status =
                          configurarStatus(item.status);

                        const IconeStatus =
                          status.icone;

                        return (
                          <tr
                            key={`${item.empresa}-${indice}`}
                            className="transition hover:bg-slate-50"
                          >
                            <td className="px-6 py-4 font-semibold">
                              {item.empresa}
                            </td>

                            <td className="px-6 py-4 text-slate-600">
                              {item.empresa_fatura ?? "—"}
                            </td>

                            <td className="px-6 py-4 font-medium">
                              {formatarValor(item.recibo)}
                            </td>

                            <td className="px-6 py-4 font-medium">
                              {formatarValor(item.fatura)}
                            </td>

                            <td className="px-6 py-4 text-xs leading-5 text-slate-500">
                              <p>
                                Recibo:{" "}
                                {item.data_recibo ?? "—"}
                              </p>

                              <p>
                                Fatura:{" "}
                                {item.data_fatura ?? "—"}
                              </p>
                            </td>

                            <td className="px-6 py-4">
                              <span
                                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-bold ${status.classes}`}
                              >
                                <IconeStatus size={14} />

                                {status.texto}
                              </span>
                            </td>
                          </tr>
                        );
                      }
                    )}
                  </tbody>
                </table>
              </div>


              <div className="divide-y divide-slate-100 md:hidden">
                {resultado.comparacao.map(
                  (item, indice) => {
                    const status =
                      configurarStatus(item.status);

                    const IconeStatus =
                      status.icone;

                    return (
                      <article
                        key={`${item.empresa}-${indice}`}
                        className="p-5"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-bold">
                              {item.empresa}
                            </p>

                            <p className="mt-1 text-sm text-slate-500">
                              {item.empresa_fatura ??
                                "Não encontrado"}
                            </p>
                          </div>

                          <span
                            className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-bold ${status.classes}`}
                          >
                            <IconeStatus size={12} />

                            {status.texto}
                          </span>
                        </div>

                        <div className="mt-4 grid grid-cols-2 gap-3">
                          <InformacaoMobile
                            titulo="Valor do recibo"
                            valor={formatarValor(
                              item.recibo
                            )}
                          />

                          <InformacaoMobile
                            titulo="Valor da fatura"
                            valor={formatarValor(
                              item.fatura
                            )}
                          />

                          <InformacaoMobile
                            titulo="Data do recibo"
                            valor={
                              item.data_recibo ?? "—"
                            }
                          />

                          <InformacaoMobile
                            titulo="Data da fatura"
                            valor={
                              item.data_fatura ?? "—"
                            }
                          />
                        </div>
                      </article>
                    );
                  }
                )}
              </div>


              {resultado.comparacao.length === 0 && (
                <div className="p-8 text-center text-slate-500">
                  Nenhuma comparação foi retornada.
                </div>
              )}
            </div>
          </div>
        </section>
      )}


      <footer className="border-t border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 sm:flex-row">
          <p className="font-semibold">
            ValidaFatura AI © 2026
          </p>

          <p className="flex items-center gap-2">
            <BrainCircuit size={16} />
            FastAPI • Next.js • OCR • Groq AI
          </p>
        </div>
      </footer>
    </main>
  );
}


type ResumoCardProps = {
  titulo: string;
  valor: number;
  descricao: string;
  classes: string;
  icone: ReactNode;
};


function ResumoCard({
  titulo,
  valor,
  descricao,
  classes,
  icone,
}: ResumoCardProps) {
  return (
    <div
      className={`rounded-2xl border p-5 shadow-sm ${classes}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">
          {titulo}
        </p>

        <div className="rounded-lg bg-white/70 p-2">
          {icone}
        </div>
      </div>

      <p className="mt-4 text-3xl font-bold">
        {valor}
      </p>

      <p className="mt-1 text-xs opacity-70">
        {descricao}
      </p>
    </div>
  );
}


type InformacaoMobileProps = {
  titulo: string;
  valor: string;
};


function InformacaoMobile({
  titulo,
  valor,
}: InformacaoMobileProps) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        {titulo}
      </p>

      <p className="mt-1 text-sm font-semibold text-slate-800">
        {valor}
      </p>
    </div>
  );
}