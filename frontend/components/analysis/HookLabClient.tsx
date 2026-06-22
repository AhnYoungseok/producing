"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchAutoBatchStatus, fetchHookSummaries, runAutoBatchNow } from "@/lib/api";
import type { AutoBatchStatus, HookSummaryRow } from "@/types/domain";

type HookRow = {
  id: string;
  title: string;
  artist: string;
  genre: string;
  addedAt: string;
  lyricHookCue: string;
  lyricFunction: string;
  hookType: string;
  hookLocation: string;
  intervalPattern: string;
  rhythmPattern: string;
  contour: string;
  lyricsStatus: string;
  lyricsUrl: string;
  whyItWorks: string;
  confidence: string;
};

export function HookLabClient() {
  const [rows, setRows] = useState<HookRow[]>([]);
  const [libraryTotal, setLibraryTotal] = useState(0);
  const [autoStatus, setAutoStatus] = useState<AutoBatchStatus | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningNow, setIsRunningNow] = useState(false);

  const load = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setIsLoading(true);
      const [hookSummary, status] = await Promise.all([fetchHookSummaries(), fetchAutoBatchStatus()]);
      setRows(hookSummary.rows.map(toHookRow));
      setLibraryTotal(hookSummary.total_count);
      setAutoStatus(status);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "후크 데이터를 불러오지 못했습니다.");
    } finally {
      if (showLoading) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialTimer = window.setTimeout(() => {
      void load(true);
    }, 0);
    const timer = window.setInterval(() => {
      void load(false);
    }, 60000);
    return () => {
      window.clearTimeout(initialTimer);
      window.clearInterval(timer);
    };
  }, [load]);

  async function runNow() {
    setIsRunningNow(true);
    setError("");
    try {
      await runAutoBatchNow(10);
      await load(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "지금 10곡 추가 실행에 실패했습니다.");
    } finally {
      setIsRunningNow(false);
    }
  }

  const usableRows = useMemo(() => rows.filter((row) => row.confidence !== "insufficient"), [rows]);

  if (isLoading) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-300">후크 데이터를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-5 text-sm text-red-100">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
        <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">Hook Lab</p>
        <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">가사 후크와 멜로디 후크</h1>
        <p className="mt-4 max-w-4xl text-sm leading-6 text-zinc-300">
          실제 곡에서 기억 장치로 작동하는 짧은 가사 단서와 멜로디 후크의 추정 간격, 리듬, 구조를 정리합니다.
          전체 가사나 전체 멜로디 채보는 저장하지 않고, 창작 연구에 필요한 구조 정보만 보여줍니다.
        </p>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <SummaryCard label="누적 곡" value={String(libraryTotal)} />
          <SummaryCard label="후크 데이터" value={String(usableRows.length)} />
          <SummaryCard label="정책" value="가사/음원 복제 없음" />
        </div>
      </section>

      <section className="rounded-lg border border-violet-500/30 bg-violet-950/20 p-5 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Auto Batch</p>
            <h2 className="mt-2 text-xl font-black text-zinc-50">10분마다 10곡 자동 누적</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              백엔드가 켜져 있는 동안 실제 히트곡 카탈로그에서 중복 없이 10곡씩 추가합니다. 화면은 1분마다 자동 새로고침됩니다.
            </p>
          </div>
          <button
            type="button"
            onClick={runNow}
            disabled={isRunningNow || Boolean(autoStatus?.running)}
            className="focus-ring rounded-lg bg-violet px-5 py-3 text-sm font-black text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
          >
            {isRunningNow || autoStatus?.running ? "추가 중..." : "지금 10곡 바로 추가"}
          </button>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <SummaryCard label="자동 상태" value={autoStatus?.enabled ? "켜짐" : "꺼짐"} />
          <SummaryCard label="간격" value={`${autoStatus?.interval_seconds ?? 600}초`} />
          <SummaryCard label="다음 실행" value={formatDateTime(autoStatus?.next_run_at)} />
          <SummaryCard label="남은 후보" value={String(autoStatus?.last_result?.queue_remaining ?? "-")} />
        </div>
        {autoStatus?.last_result?.songs?.length ? (
          <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs leading-5 text-zinc-300">
            <p className="font-bold text-zinc-100">
              마지막 자동 추가: {autoStatus.last_result.imported_count}곡 · 현재 누적 {autoStatus.last_result.total_after}곡
            </p>
            <p className="mt-1 text-zinc-500">
              {autoStatus.last_result.songs
                .map((song) => `${song.title} - ${song.artist || "Unknown"} (${formatDate(autoStatus.last_run_at)})`)
                .join(", ")}
            </p>
          </div>
        ) : null}
        {autoStatus?.last_error ? <p className="mt-3 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-100">{autoStatus.last_error}</p> : null}
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900 shadow-2xl">
        <div className="overflow-x-auto">
          <table className="min-w-[1440px] divide-y divide-zinc-800 text-left text-sm">
            <thead className="bg-zinc-950 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <Th>곡</Th>
                <Th>추가일</Th>
                <Th>가사 후크 단서</Th>
                <Th>후크 기능</Th>
                <Th>멜로디 간격</Th>
                <Th>멜로디 리듬</Th>
                <Th>후크 위치</Th>
                <Th>가사 전문</Th>
                <Th>왜 기억되는가</Th>
                <Th>신뢰도</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {rows.map((row) => (
                <tr key={row.id} className="align-top hover:bg-zinc-950/70">
                  <td className="w-56 px-4 py-4">
                    <Link href={`/songs/${row.id}`} className="font-black text-zinc-50 hover:text-cyan-200">
                      {row.title}
                    </Link>
                    <p className="mt-1 text-xs text-zinc-500">{row.artist}</p>
                    <p className="mt-1 text-[11px] text-zinc-600">{row.genre}</p>
                  </td>
                  <td className="w-28 px-4 py-4 text-xs font-bold text-zinc-400">{row.addedAt}</td>
                  <td className="w-44 px-4 py-4 font-bold text-cyan-100">{row.lyricHookCue}</td>
                  <td className="w-64 px-4 py-4 leading-6 text-zinc-300">{row.lyricFunction}</td>
                  <td className="w-56 px-4 py-4 leading-6 text-zinc-300">{row.intervalPattern}</td>
                  <td className="w-56 px-4 py-4 leading-6 text-zinc-300">{row.rhythmPattern}</td>
                  <td className="w-44 px-4 py-4 leading-6 text-zinc-300">{row.hookLocation}</td>
                  <td className="w-48 px-4 py-4 leading-6 text-zinc-300">
                    <p>{row.lyricsStatus}</p>
                    <a href={row.lyricsUrl} target="_blank" rel="noreferrer" className="mt-2 inline-block rounded border border-zinc-700 px-2 py-1 text-xs font-bold text-cyan-100 hover:border-cyan-400">
                      공식 가사 검색
                    </a>
                  </td>
                  <td className="w-72 px-4 py-4 leading-6 text-zinc-300">{row.whyItWorks}</td>
                  <td className="w-28 px-4 py-4">
                    <span className={`rounded px-2 py-1 text-[11px] font-black uppercase ${confidenceClass(row.confidence)}`}>{row.confidence}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-4 text-sm leading-6 text-amber-100">
        자동 누적 곡에는 저작권 보호 가사 전문을 저장하지 않습니다. 곡 상세 페이지에서 사용자가 직접 제공한 가사는 실제 텍스트로 표시하고 분석합니다.
        가사 후크는 10단어 이하의 짧은 단서만 표시하며, 멜로디 후크는 실제 선율 복제가 아니라 추정 간격, 리듬 방향, 구조 정보로만 제공합니다.
      </p>
    </div>
  );
}

function toHookRow(row: HookSummaryRow): HookRow {
  return {
    id: row.id,
    title: row.title,
    artist: row.artist || "Unknown Artist",
    genre: row.genre || "Unknown",
    addedAt: formatDate(row.created_at),
    lyricHookCue: row.lyric_hook_cue,
    lyricFunction: row.lyric_function,
    hookType: row.hook_type,
    hookLocation: row.hook_location,
    intervalPattern: row.interval_pattern,
    rhythmPattern: row.rhythm_pattern,
    contour: row.contour,
    lyricsStatus: row.lyrics_status,
    lyricsUrl: row.lyrics_url,
    whyItWorks: row.why_it_works,
    confidence: row.confidence
  };
}

function confidenceClass(confidence: string) {
  if (confidence === "high") return "bg-emerald-500/15 text-emerald-200";
  if (confidence === "medium") return "bg-cyan-500/15 text-cyan-200";
  if (confidence === "insufficient") return "bg-red-500/15 text-red-200";
  return "bg-amber-500/15 text-amber-200";
}

function formatDate(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(date);
}

function formatDateTime(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(date);
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-zinc-50">{value}</p>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-black">{children}</th>;
}
