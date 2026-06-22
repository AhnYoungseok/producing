"use client";

import { useEffect, useState } from "react";

import { SongCard } from "@/components/cards/SongCard";
import { GenreBestsellerImportPanel } from "@/components/research/GenreBestsellerImportPanel";
import { extractPatterns, fetchPatterns, fetchSongs } from "@/lib/api";
import type { GenreBestsellerImportResponse, Pattern, Song } from "@/types/domain";

const PATTERN_TYPES = [
  ["concept", "컨셉"],
  ["lyrics", "가사"],
  ["harmony", "코드"],
  ["melody", "멜로디"],
  ["hook", "후크"],
  ["structure", "구조"],
  ["arrangement", "편곡"],
  ["vocal", "보컬"],
  ["mixing", "믹싱"],
  ["hit_factor", "히트 포인트"]
] as const;

export function PatternLabClient() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [selectedSongIds, setSelectedSongIds] = useState<string[]>([]);
  const [patternTypes, setPatternTypes] = useState<string[]>(["concept", "lyrics", "harmony", "hook", "arrangement"]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    Promise.all([fetchSongs(), fetchPatterns()])
      .then(([songData, patternData]) => {
        setSongs(songData.filter((song) => song.analysis_complete));
        setPatterns(patternData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Pattern Lab 데이터를 불러오지 못했습니다."));
  }, []);

  function toggleSong(id: string) {
    setSelectedSongIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  function toggleType(type: string) {
    setPatternTypes((current) => (current.includes(type) ? current.filter((item) => item !== type) : [...current, type]));
  }

  async function onExtract() {
    setError("");
    setIsLoading(true);
    try {
      const extracted = await extractPatterns(selectedSongIds, patternTypes);
      setPatterns((current) => [...extracted, ...current]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "패턴 추출 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  async function onBestsellerImportComplete(result: GenreBestsellerImportResponse) {
    const [songData, patternData] = await Promise.all([fetchSongs(), fetchPatterns()]);
    setSongs(songData.filter((song) => song.analysis_complete));
    setPatterns(patternData);
    setSelectedSongIds(result.songs.map((song) => song.id));
  }

  return (
    <div className="space-y-6">
      <GenreBestsellerImportPanel onComplete={onBestsellerImportComplete} />

      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
        <h2 className="text-lg font-black text-zinc-50">분석할 패턴 유형</h2>
        <p className="mt-2 text-sm leading-6 text-zinc-400">선택한 곡들에서 공통적으로 반복되는 창작 원리를 찾습니다.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {PATTERN_TYPES.map(([type, label]) => (
            <button key={type} type="button" onClick={() => toggleType(type)} className={`focus-ring rounded-lg px-3 py-2 text-xs font-bold ${patternTypes.includes(type) ? "bg-cyan-400 text-zinc-950" : "border border-zinc-700 text-zinc-300"}`}>
              {label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-black text-zinc-50">분석곡 선택</h2>
          <button disabled={isLoading || selectedSongIds.length === 0 || patternTypes.length === 0} onClick={onExtract} className="focus-ring rounded-lg bg-violet px-5 py-2.5 text-sm font-bold text-white disabled:bg-zinc-700 disabled:text-zinc-400">
            {isLoading ? "추출 중..." : "공통 패턴 추출"}
          </button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {songs.length === 0 ? <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-400">패턴을 추출하려면 먼저 분석 완료된 곡이 필요합니다.</div> : null}
          {songs.map((song) => (
            <SongCard key={song.id} song={song} selectable selected={selectedSongIds.includes(song.id)} onToggle={toggleSong} />
          ))}
        </div>
      </section>

      {error ? <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="grid gap-4 lg:grid-cols-2">
        {patterns.map((pattern) => (
          <article key={pattern.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
            <p className="text-xs font-bold uppercase tracking-wide text-cyan-300">{pattern.pattern_type}</p>
            <h3 className="mt-2 text-lg font-black text-zinc-50">{pattern.description}</h3>
            <p className="mt-3 text-sm text-zinc-400">Source songs: {pattern.source_song_ids.length}</p>
            <pre className="mt-4 max-h-56 overflow-auto rounded-lg bg-zinc-950 p-3 text-xs leading-5 text-zinc-300">{JSON.stringify(pattern.pattern_json, null, 2)}</pre>
          </article>
        ))}
      </section>
    </div>
  );
}
