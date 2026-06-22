"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { fetchComposerState, sendComposerMessage } from "@/lib/api";
import type { Blueprint, ComposerMessage, ComposerOption, Project } from "@/types/domain";

const CONVERSATION_STEPS = [
  "곡의 방향",
  "장르와 감정",
  "레퍼런스 추천",
  "공통 패턴",
  "컨셉",
  "제목과 가사",
  "감정선",
  "곡 구조",
  "코드 진행",
  "멜로디",
  "후크",
  "리듬/그루브",
  "편곡",
  "보컬",
  "믹싱",
  "최종 가이드"
];

const BLUEPRINT_CARDS = [
  ["concept", "1. 컨셉"],
  ["emotion_curve", "2. 감정선"],
  ["structure_plan", "3. 곡 구조"],
  ["title_candidates", "4. 제목 후보"],
  ["lyrics_direction", "5. 가사 설계"],
  ["harmony_plan", "6. 코드 진행"],
  ["melody_direction", "7. 멜로디 방향"],
  ["hook_plan", "8. 후크"],
  ["rhythm_groove", "9. 리듬/그루브"],
  ["arrangement_direction", "10. 편곡"],
  ["vocal_production", "11. 보컬 프로덕션"],
  ["sound_mixing", "12. 사운드/믹싱"],
  ["final_production_guide", "최종 제작 가이드"]
] as const;

export function ComposerCoachClient({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [messages, setMessages] = useState<ComposerMessage[]>([]);
  const [options, setOptions] = useState<ComposerOption[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;

    fetchComposerState(projectId)
      .then(async (state) => {
        if (!active) return;
        const initialHistory = readMessages(state.blueprint.blueprint_json);
        setProject(state.project);
        setBlueprint(state.blueprint);
        setMessages(initialHistory);
        setOptions(readOptions(state.blueprint.blueprint_json));

        if (initialHistory.length === 0) {
          const response = await sendComposerMessage(projectId, {});
          if (!active) return;
          setBlueprint(response.blueprint);
          setMessages(readMessages(response.blueprint.blueprint_json));
          setOptions(response.options);
        }
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Composer Coach를 불러오지 못했습니다.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [projectId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  const data = blueprint?.blueprint_json;
  const currentStage = typeof data?.current_stage === "number" ? data.current_stage : 1;
  const currentStageLabel = CONVERSATION_STEPS[Math.max(0, Math.min(currentStage - 1, CONVERSATION_STEPS.length - 1))];
  const filledCards = useMemo(() => BLUEPRINT_CARDS.filter(([key]) => hasContent(data?.[key])), [data]);

  async function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) return;
    setInput("");
    await sendTurn({ message });
  }

  async function selectOption(option: ComposerOption) {
    if (isSending) return;
    await sendTurn({ selected_option_id: option.id });
  }

  async function sendTurn(payload: { message?: string; selected_option_id?: string }) {
    setError("");
    setIsSending(true);
    try {
      const response = await sendComposerMessage(projectId, payload);
      setBlueprint(response.blueprint);
      setMessages(readMessages(response.blueprint.blueprint_json));
      setOptions(response.options);
    } catch (err) {
      setError(err instanceof Error ? err.message : "대화 처리 중 오류가 발생했습니다.");
    } finally {
      setIsSending(false);
    }
  }

  if (isLoading) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-300">Composer Coach 준비 중...</div>;
  }

  if (error && !project) {
    return <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-5 text-sm text-red-100">{error}</div>;
  }

  if (!project || !data) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-300">프로젝트 정보를 찾을 수 없습니다.</div>;
  }

  return (
    <div className="space-y-6">
      <section className="border-b border-zinc-800 pb-6">
        <p className="text-sm font-black uppercase tracking-[0.24em] text-cyan-300">Composer Coach</p>
        <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-black text-zinc-50 sm:text-5xl">{project.title}</h1>
            <p className="mt-3 text-sm leading-6 text-zinc-400">
              {project.target_genre || "장르 미정"} · {project.target_mood || "감정 미정"} · 현재 {currentStage}/16단계: {currentStageLabel}
            </p>
          </div>
          <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 px-4 py-3 text-xs leading-5 text-cyan-100">
            기존 곡을 복제하지 않고, 공통 창작 원리를 새 표현으로 바꿔 설계합니다.
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.25fr)]">
        <div className="flex min-h-[680px] flex-col rounded-lg border border-zinc-800 bg-zinc-950 shadow-2xl">
          <div className="border-b border-zinc-800 p-4">
            <p className="text-xs font-black uppercase tracking-[0.24em] text-violet-300">AI Lab Chat</p>
            <h2 className="mt-2 text-xl font-black text-zinc-50">{currentStageLabel}</h2>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((message, index) => (
              <ChatBubble key={`${message.created_at ?? index}-${message.role}`} message={message} />
            ))}
            <div ref={scrollRef} />
          </div>

          {options.length > 0 ? (
            <div className="border-t border-zinc-800 p-4">
              <div className="grid gap-2">
                {options.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => selectOption(option)}
                    disabled={isSending}
                    className="focus-ring rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-left transition hover:border-cyan-400 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className="block text-sm font-black text-zinc-50">{option.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-zinc-400">{option.summary}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <form onSubmit={submitMessage} className="border-t border-zinc-800 p-4">
            <label htmlFor="composer-message" className="sr-only">
              Composer Coach 메시지
            </label>
            <textarea
              id="composer-message"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              rows={3}
              placeholder="원하는 방향, 수정할 점, 직접 선택한 아이디어를 입력하세요."
              className="focus-ring w-full resize-none rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-sm leading-6 text-zinc-100 placeholder:text-zinc-600"
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              className="focus-ring mt-3 w-full rounded-lg bg-cyan-400 px-5 py-3 text-sm font-black text-zinc-950 transition hover:bg-cyan-300 disabled:bg-zinc-700 disabled:text-zinc-400"
            >
              {isSending ? "반영 중..." : "메시지 보내기"}
            </button>
            {error ? <p className="mt-3 text-sm text-red-200">{error}</p> : null}
          </form>
        </div>

        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="현재 단계" value={`${currentStage}/16`} />
            <Metric label="선택 기록" value={`${Array.isArray(data.decisions) ? data.decisions.length : 0}개`} />
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            {(filledCards.length > 0 ? filledCards : BLUEPRINT_CARDS.slice(0, 6)).map(([key, label]) => (
              <BlueprintCard key={key} title={label} value={data[key]} large={key === "final_production_guide"} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function ChatBubble({ message }: { message: ComposerMessage }) {
  const isAssistant = message.role === "assistant";
  return (
    <article className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[88%] rounded-lg border px-4 py-3 text-sm leading-6 ${
          isAssistant
            ? "border-zinc-800 bg-zinc-900 text-zinc-100"
            : "border-cyan-500/40 bg-cyan-950/50 text-cyan-50"
        }`}
      >
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.2em] text-zinc-500">
          {isAssistant ? "AI Producer" : "You"}
        </p>
        <p className="whitespace-pre-line">{message.content}</p>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <p className="text-xs font-bold text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-zinc-50">{value}</p>
    </div>
  );
}

function BlueprintCard({ title, value, large }: { title: string; value: unknown; large?: boolean }) {
  return (
    <article className={`rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl ${large ? "xl:col-span-2" : ""}`}>
      <h2 className="text-sm font-black text-zinc-50">{title}</h2>
      <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-zinc-950 p-3 text-xs leading-5 text-zinc-300">{formatValue(value)}</pre>
    </article>
  );
}

function readMessages(data: Record<string, unknown>): ComposerMessage[] {
  const history = data.conversation_history;
  if (!Array.isArray(history)) return [];
  return history.filter(isComposerMessage);
}

function readOptions(data: Record<string, unknown>): ComposerOption[] {
  const rawOptions = data.last_options;
  if (!Array.isArray(rawOptions)) return [];
  return rawOptions.filter(isComposerOption);
}

function isComposerMessage(value: unknown): value is ComposerMessage {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (item.role === "user" || item.role === "assistant") && typeof item.content === "string";
}

function isComposerOption(value: unknown): value is ComposerOption {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return typeof item.id === "string" && typeof item.label === "string" && typeof item.summary === "string";
}

function hasContent(value: unknown): boolean {
  if (value == null) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}

function formatValue(value: unknown): string {
  if (typeof value === "string") return value || "아직 정리 전입니다.";
  if (Array.isArray(value)) {
    if (value.length === 0) return "아직 정리 전입니다.";
    if (value.every((item) => typeof item === "string")) return value.map((item) => `- ${item}`).join("\n");
    return JSON.stringify(value, null, 2);
  }
  if (value && typeof value === "object" && Object.keys(value).length > 0) {
    return JSON.stringify(value, null, 2);
  }
  return "아직 정리 전입니다.";
}
