"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { fetchGenreBestsellerCatalog, importGenreBestsellers } from "@/lib/api";
import type { GenreBestsellerCatalogItem, GenreBestsellerImportResponse } from "@/types/domain";

type Props = {
  onComplete?: (result: GenreBestsellerImportResponse) => void;
  compact?: boolean;
};

export function GenreBestsellerImportPanel({ onComplete, compact = false }: Props) {
  const [genres, setGenres] = useState<GenreBestsellerCatalogItem[]>([]);
  const [selectedGenre, setSelectedGenre] = useState("K-pop Ballad");
  const [result, setResult] = useState<GenreBestsellerImportResponse | null>(null);
  const [error, setError] = useState("");
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    fetchGenreBestsellerCatalog()
      .then((items) => {
        setGenres(items);
        if (items[0]?.genre) {
          setSelectedGenre(items[0].genre);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "장르별 Top 10 카탈로그를 불러오지 못했습니다."));
  }, []);

  async function onImport() {
    setError("");
    setResult(null);
    setIsImporting(true);
    try {
      const imported = await importGenreBestsellers(selectedGenre, 10);
      setResult(imported);
      onComplete?.(imported);
    } catch (err) {
      setError(err instanceof Error ? err.message : "장르별 Top 10 자동 분석 중 오류가 발생했습니다.");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <section className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 p-5">
      <div className={compact ? "space-y-4" : "grid gap-5 lg:grid-cols-[1.2fr_0.8fr]"}>
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-cyan-300">Hit Song Research Mode</p>
          <h2 className="mt-2 text-xl font-black text-zinc-50">장르별 히트곡 연구 데이터 자동 누적</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-300">
            장르별 대표 히트곡을 Song Library에 쌓고, 코드 진행, 후크, 가사 주제, 편곡, 보컬, 믹싱 특징을 통계에 반영합니다.
            같은 곡을 번호만 바꿔 반복 저장하지 않으며, 이미 있는 곡은 신규로 세지 않고 기존 분석을 갱신합니다.
          </p>
          <p className="mt-2 text-xs leading-5 text-zinc-500">
            YouTube 링크는 레퍼런스 시작점으로만 사용합니다. YouTube 오디오는 다운로드, 추출, 분리, 변환, 캡처, 분석하지 않습니다.
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
          <label className="text-xs font-bold text-zinc-400" htmlFor="bestseller-genre">
            분석할 장르
          </label>
          <select
            id="bestseller-genre"
            value={selectedGenre}
            onChange={(event) => setSelectedGenre(event.target.value)}
            className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
          >
            {genres.map((item) => (
              <option key={item.genre} value={item.genre}>
                {item.genre} ({item.song_count}곡)
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={isImporting || !selectedGenre}
            onClick={onImport}
            className="focus-ring mt-4 w-full rounded-lg bg-cyan-400 px-5 py-3 text-sm font-black text-zinc-950 disabled:bg-zinc-700 disabled:text-zinc-400"
          >
            {isImporting ? "Top 10 분석 중..." : "Top 10 자동 분석하고 통계 내기"}
          </button>
          <p className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs leading-5 text-zinc-400">
            대량 통계는 10분 자동 작업이 중복 없는 실제 히트곡을 10곡씩 누적하는 방식으로만 확장합니다.
          </p>
          {result ? (
            <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900 p-3 text-xs leading-5 text-zinc-300">
              <p className="font-bold text-zinc-100">
                {result.genre} {result.imported_count}곡 반영 완료
              </p>
              <p>
                신규 {result.created_count}곡, 기존 갱신 {result.reused_count}곡
              </p>
              <p>장르 평균 BPM: {result.genre_statistics.summary.average_bpm}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link href="/library" className="rounded border border-zinc-700 px-2 py-1 font-bold text-zinc-200">
                  Song Library 보기
                </Link>
                <Link href="/patterns" className="rounded border border-zinc-700 px-2 py-1 font-bold text-zinc-200">
                  통계/패턴 보기
                </Link>
              </div>
            </div>
          ) : null}
          {error ? <div className="mt-4 rounded-lg border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-100">{error}</div> : null}
        </div>
      </div>
    </section>
  );
}
