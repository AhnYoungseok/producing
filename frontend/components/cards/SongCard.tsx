import Link from "next/link";

import type { Song } from "@/types/domain";

export function SongCard({ song, selectable, selected, onToggle }: { song: Song; selectable?: boolean; selected?: boolean; onToggle?: (id: string) => void }) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="line-clamp-2 text-lg font-black text-zinc-50">{song.title}</h3>
          <p className="mt-1 text-sm text-zinc-500">{song.artist || "아티스트 미상"}</p>
          <p className="mt-2 text-xs font-bold text-zinc-600">추가일 {formatDate(song.created_at)}</p>
        </div>
        {selectable ? (
          <button
            type="button"
            onClick={() => onToggle?.(song.id)}
            className={`focus-ring rounded-lg px-3 py-1.5 text-xs font-bold ${
              selected ? "bg-cyan-400 text-zinc-950" : "border border-zinc-700 text-zinc-300"
            }`}
          >
            {selected ? "선택됨" : "선택"}
          </button>
        ) : null}
      </div>
      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <Metric label="장르" value={song.genre || "Unknown"} />
        <Metric label="국가" value={song.country || "Unknown"} />
        <Metric label="BPM" value={song.bpm ? song.bpm.toFixed(1) : "-"} />
        <Metric label="Key" value={song.key || "-"} />
      </dl>
      <div className="mt-5 flex items-center justify-between gap-3">
        <span className={`rounded px-2 py-1 text-xs font-bold ${song.analysis_complete ? "bg-emerald-500/15 text-emerald-200" : "bg-zinc-800 text-zinc-400"}`}>
          {song.analysis_complete ? "분석 완료" : "등록됨"}
        </span>
        <Link href={`/songs/${song.id}`} className="focus-ring rounded-lg bg-violet px-4 py-2 text-sm font-bold text-white transition hover:bg-violet-500">
          상세보기
        </Link>
      </div>
    </article>
  );
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2">
      <dt className="text-xs font-semibold text-zinc-500">{label}</dt>
      <dd className="mt-1 truncate font-bold text-zinc-100">{value}</dd>
    </div>
  );
}
