"use client";

import { FormEvent, useEffect, useState } from "react";

import { SongCard } from "@/components/cards/SongCard";
import { fetchSongs } from "@/lib/api";
import type { Song } from "@/types/domain";

export function LibraryClient() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadSongs();
  }, []);

  async function loadSongs(params?: URLSearchParams) {
    try {
      setSongs(await fetchSongs(params));
    } catch (err) {
      setError(err instanceof Error ? err.message : "곡 목록을 불러오지 못했습니다.");
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("query", query.trim());
    if (genre.trim()) params.set("genre", genre.trim());
    loadSongs(params);
  }

  return (
    <div className="space-y-5">
      <form onSubmit={onSubmit} className="grid gap-3 rounded-lg border border-zinc-800 bg-zinc-900 p-4 md:grid-cols-[1fr_220px_auto]">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="곡 제목 또는 아티스트 검색" className="focus-ring rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-100" />
        <input value={genre} onChange={(event) => setGenre(event.target.value)} placeholder="장르 필터" className="focus-ring rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-100" />
        <button className="focus-ring rounded-lg bg-cyan-400 px-5 py-2.5 text-sm font-black text-zinc-950">필터 적용</button>
      </form>
      {error ? <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-100">{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {songs.length === 0 ? <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-400">저장된 곡이 없습니다.</div> : null}
        {songs.map((song) => (
          <SongCard key={song.id} song={song} />
        ))}
      </div>
    </div>
  );
}
