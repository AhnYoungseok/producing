"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { SongCard } from "@/components/cards/SongCard";
import { StatCard } from "@/components/cards/StatCard";
import { ChartPanel } from "@/components/charts/ChartPanel";
import { GenreBestsellerImportPanel } from "@/components/research/GenreBestsellerImportPanel";
import { exportLibrary, fetchDashboard, fetchSongs, fetchStatistics, importNextReferenceBatch } from "@/lib/api";
import type { ChartDataset, Dashboard, HitSongStatistics, NextReferenceBatchResponse, Song } from "@/types/domain";

const PRIMARY_CHART_KEYS = [
  "by_genre",
  "bpm_distribution",
  "top_keys",
  "top_verse_progressions",
  "top_pre_chorus_progressions",
  "top_chorus_progressions",
  "top_bridge_progressions",
  "top_song_structures",
  "hook_type_distribution",
  "top_mood_keywords",
  "top_lyric_themes",
  "top_arrangement_features",
  "top_vocal_treatments",
  "top_hit_factors",
  "top_transferable_principles"
];

export function DashboardClient() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [statistics, setStatistics] = useState<HitSongStatistics | null>(null);
  const [allSongs, setAllSongs] = useState<Song[]>([]);
  const [error, setError] = useState("");
  const [exportMessage, setExportMessage] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [batchResult, setBatchResult] = useState<NextReferenceBatchResponse | null>(null);
  const [batchError, setBatchError] = useState("");
  const [isBatchImporting, setIsBatchImporting] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const [dashboardData, statisticsData, songData] = await Promise.all([fetchDashboard(), fetchStatistics(), fetchSongs()]);
      setDashboard(dashboardData);
      setStatistics(statisticsData);
      setAllSongs(songData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "대시보드 데이터를 불러오지 못했습니다.");
    }
  }

  async function importNewHitSongBatch() {
    setBatchError("");
    setBatchResult(null);
    setIsBatchImporting(true);
    try {
      const result = await importNextReferenceBatch(10);
      setBatchResult(result);
      await loadDashboard();
    } catch (err) {
      setBatchError(err instanceof Error ? err.message : "새 히트곡 10곡 분석 중 오류가 발생했습니다.");
    } finally {
      setIsBatchImporting(false);
    }
  }

  const chartDatasets = useMemo(() => {
    if (!statistics?.chart_datasets) return [];
    return PRIMARY_CHART_KEYS.map((key) => statistics.chart_datasets?.[key]).filter(Boolean) as ChartDataset[];
  }, [statistics]);

  if (error) {
    return <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-5 text-sm text-red-100">{error}</div>;
  }
  if (!dashboard || !statistics) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-300">불러오는 중...</div>;
  }

  const titleRatio = Math.round((statistics.summary.title_in_chorus_ratio ?? statistics.title_in_chorus_ratio ?? 0) * 100);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ModeCard title="YouTube Reference Analysis" body="링크에서 레퍼런스곡을 등록하고 허용된 메타데이터와 사용자 입력을 분석 데이터로 정리합니다." />
        <ModeCard title="Chord and Structure Analysis" body="BPM, Key, 코드 진행, 곡 구조, 후크 위치를 누적해 장르별 패턴을 계산합니다." />
        <ModeCard title="Producer Research Mode" body="편곡, 보컬, 믹싱, 히트 포인트를 프로듀서 관점의 feature field로 저장합니다." />
        <ModeCard title="Hit Song Research Mode" body="여러 곡의 통계를 모아 새 노래 설계에 사용할 창작 원리로 일반화합니다." />
      </section>

      <GenreBestsellerImportPanel compact onComplete={() => loadDashboard()} />

      <section className="rounded-lg border border-violet-500/30 bg-violet-950/20 p-5 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">One Click Batch</p>
            <h2 className="mt-2 text-xl font-black text-zinc-50">새 히트곡 10곡 분석·누적</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              버튼을 누르면 중복 없는 국내외 히트곡 10곡을 새로 등록하고, BPM, Key, 코드 진행, 가사 주제, 후크, 편곡, 보컬,
              믹싱, 히트 포인트를 DB와 통계에 반영합니다.
            </p>
            <p className="mt-2 text-xs leading-5 text-zinc-500">
              YouTube는 레퍼런스 식별용 링크로만 사용하며, YouTube 오디오는 다운로드하거나 추출하지 않습니다.
            </p>
          </div>
          <button
            type="button"
            onClick={importNewHitSongBatch}
            disabled={isBatchImporting}
            className="focus-ring rounded-lg bg-violet px-5 py-3 text-sm font-black text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
          >
            {isBatchImporting ? "10곡 분석 중..." : "새로운 곡 10곡 분석하기"}
          </button>
        </div>
        {batchResult ? (
          <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm leading-6 text-zinc-300">
            <p className="font-bold text-zinc-50">
              {batchResult.imported_count}곡 추가 완료 · 현재 누적 {batchResult.total_after}곡
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {batchResult.songs.map((song) => (
                <Link key={song.id} href={`/songs/${song.id}`} className="rounded border border-zinc-700 px-2 py-1 text-xs font-bold text-zinc-200 hover:border-violet-400">
                  {song.title} · {song.artist || "Unknown"}
                </Link>
              ))}
            </div>
            {batchResult.low_confidence.length > 0 ? (
              <p className="mt-3 text-xs text-amber-200">저신뢰 필드: {batchResult.low_confidence.join(", ")}</p>
            ) : (
              <p className="mt-3 text-xs text-emerald-200">이번 배치에는 low confidence 항목이 없습니다.</p>
            )}
            <p className="mt-2 text-xs text-zinc-500">남은 신규 큐 후보: {batchResult.queue_remaining}곡</p>
          </div>
        ) : null}
        {batchError ? <div className="mt-4 rounded-lg border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-100">{batchError}</div> : null}
      </section>

      <section className="rounded-lg border border-cyan-500/20 bg-zinc-900 p-5 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Song Feature Database</p>
            <h2 className="mt-2 text-xl font-black text-zinc-50">장르별 곡 데이터 저장소</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-400">
              분석 데이터는 DB에 저장되고, PC의 `backend/exports/hit_song_library` 폴더에 장르별 CSV/JSON으로 누적됩니다.
              이 파일은 Excel, Google Sheets, GitHub에서 바로 다룰 수 있습니다.
            </p>
          </div>
          <button
            type="button"
            onClick={async () => {
              setIsExporting(true);
              setExportMessage("");
              try {
                const result = await exportLibrary();
                setExportMessage(`${result.total_songs}곡 · ${result.genre_count}개 장르 export 완료: ${result.export_root}`);
              } catch (err) {
                setExportMessage(err instanceof Error ? err.message : "export에 실패했습니다.");
              } finally {
                setIsExporting(false);
              }
            }}
            className="focus-ring rounded-lg bg-cyan-500 px-4 py-3 text-sm font-black text-zinc-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isExporting}
          >
            {isExporting ? "내보내는 중..." : "장르별 CSV 내보내기"}
          </button>
        </div>
        {exportMessage ? <p className="mt-4 rounded border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm leading-6 text-zinc-200">{exportMessage}</p> : null}
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-300">Analyzed Song Titles</p>
            <h2 className="mt-2 text-2xl font-black text-zinc-50">분석된 전체 곡명 {allSongs.length}곡</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-400">
              지금까지 DB에 누적된 모든 분석 곡명입니다. 클릭하면 곡별 상세 분석으로 이동합니다.
            </p>
          </div>
          <Link href="/library" className="focus-ring rounded-lg border border-zinc-700 px-4 py-2 text-sm font-bold text-zinc-100">
            Song Library 전체 보기
          </Link>
        </div>
        <div className="mt-5 max-h-[520px] overflow-auto rounded-lg border border-zinc-800 bg-zinc-950">
          <div className="grid min-w-[760px] grid-cols-[64px_1.4fr_1fr_1fr_88px_88px] border-b border-zinc-800 bg-zinc-900 px-4 py-3 text-xs font-black uppercase tracking-wide text-zinc-400">
            <span>No.</span>
            <span>곡명</span>
            <span>아티스트</span>
            <span>장르</span>
            <span>BPM</span>
            <span>Key</span>
          </div>
          {allSongs.map((song, index) => (
            <Link
              key={song.id}
              href={`/songs/${song.id}`}
              className="grid min-w-[760px] grid-cols-[64px_1.4fr_1fr_1fr_88px_88px] border-b border-zinc-900 px-4 py-3 text-sm text-zinc-300 hover:bg-zinc-900/80"
            >
              <span className="text-zinc-500">{index + 1}</span>
              <span className="font-bold text-zinc-100">{song.title}</span>
              <span>{song.artist || "Unknown"}</span>
              <span>{song.genre || "Unknown"}</span>
              <span>{song.bpm ?? "-"}</span>
              <span>{song.key || "-"}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="저장된 Reference Songs" value={dashboard.song_count} caption="Song Library에 누적된 연구 데이터" />
        <StatCard label="분석 완료 곡" value={statistics.summary.analyzed_song_count} caption="프로듀서 리포트가 생성된 곡" />
        <StatCard label="평균 BPM" value={statistics.summary.average_bpm || "-"} caption="Reference Song Analysis 기준 중심 템포" />
        <StatCard label="제목-후렴 연결" value={`${titleRatio}%`} caption="제목이 후렴에 등장하는 비율" />
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Pattern Summaries</p>
            <h2 className="mt-2 text-2xl font-black text-zinc-50">차트에서 읽은 프로듀서 패턴</h2>
          </div>
          <Link href="/patterns" className="focus-ring rounded-lg border border-zinc-700 px-4 py-2 text-sm font-bold text-zinc-100">
            Pattern Lab 열기
          </Link>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {(statistics.pattern_summaries ?? []).map((item) => (
            <article key={item.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-black text-zinc-50">{item.title}</h3>
                <span className={`rounded px-2 py-1 text-[11px] font-black uppercase ${confidenceClass(item.confidence)}`}>{item.confidence}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-cyan-100">{item.summary}</p>
              <p className="mt-2 text-xs leading-5 text-zinc-500">{item.producer_takeaway}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-4">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Charts</p>
          <h2 className="mt-2 text-2xl font-black text-zinc-50">Reference Song Analysis 차트</h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {chartDatasets.map((dataset) => (
            <ChartPanel key={dataset.id} dataset={dataset} />
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Feature Fields</p>
        <h2 className="mt-2 text-2xl font-black text-zinc-50">Song Feature Database 설계</h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {(statistics.feature_schema ?? []).map((group) => (
            <article key={group.category} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
              <h3 className="text-sm font-black text-zinc-50">{group.category}</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {group.fields.map((field) => (
                  <span key={field} className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-300">
                    {field}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-xl font-black text-zinc-50">최근 저장된 레퍼런스곡</h2>
          <Link href="/analyze" className="focus-ring rounded-lg bg-violet px-4 py-2 text-sm font-bold text-white">
            새 Reference Song 분석
          </Link>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {dashboard.recent_songs.length === 0 ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-400">아직 저장된 분석곡이 없습니다.</div>
          ) : null}
          {dashboard.recent_songs.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      </section>
    </div>
  );
}

function ModeCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <h2 className="text-sm font-black text-zinc-50">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-zinc-400">{body}</p>
    </article>
  );
}

function confidenceClass(confidence: string) {
  if (confidence === "high") return "bg-emerald-500/15 text-emerald-200";
  if (confidence === "medium") return "bg-cyan-500/15 text-cyan-200";
  return "bg-amber-500/15 text-amber-200";
}
