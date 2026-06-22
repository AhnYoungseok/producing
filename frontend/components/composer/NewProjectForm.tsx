"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";

import { SongCard } from "@/components/cards/SongCard";
import { createProject, fetchSongs } from "@/lib/api";
import type { Song } from "@/types/domain";

type ProjectValues = {
  title: string;
  target_genre: string;
  target_mood: string;
  target_listener: string;
  theme: string;
  vocal_style: string;
  bpm_range: string;
  lyric_language: string;
  instruments: string;
  arrangement_style: string;
};

export function NewProjectForm() {
  const router = useRouter();
  const { register, handleSubmit } = useForm<ProjectValues>({ defaultValues: { lyric_language: "한국어" } });
  const [songs, setSongs] = useState<Song[]>([]);
  const [selectedSongIds, setSelectedSongIds] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchSongs()
      .then((items) => setSongs(items.filter((song) => song.analysis_complete)))
      .catch((err) => setError(err instanceof Error ? err.message : "참고곡을 불러오지 못했습니다."));
  }, []);

  function toggleSong(id: string) {
    setSelectedSongIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  async function onSubmit(values: ProjectValues) {
    setError("");
    setIsSubmitting(true);
    try {
      const project = await createProject({
        ...values,
        reference_song_ids: selectedSongIds
      });
      router.push(`/composer/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로젝트 생성 중 오류가 발생했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <section className="grid gap-4 rounded-lg border border-zinc-800 bg-zinc-900 p-5 md:grid-cols-2">
        <Field label="프로젝트 제목" placeholder="예: 늦은 밤 회상형 발라드" registration={register("title", { required: true })} />
        <Field label="만들고 싶은 장르" placeholder="예: K-pop Ballad" registration={register("target_genre")} />
        <Field label="원하는 감정" placeholder="예: 그리움, 담담함, 회상" registration={register("target_mood")} />
        <Field label="목표 청자" placeholder="예: 30-50대 감성 발라드 청자" registration={register("target_listener")} />
        <Field label="곡의 주제" placeholder="예: 지나간 사랑을 늦은 밤에 돌아봄" registration={register("theme")} />
        <Field label="보컬 스타일" placeholder="예: 가까이 말하듯 시작하는 여성 보컬" registration={register("vocal_style")} />
        <Field label="BPM 범위" placeholder="예: 68-78" registration={register("bpm_range")} />
        <Field label="가사 언어" placeholder="예: 한국어" registration={register("lyric_language")} />
        <Field label="사용 악기" placeholder="예: piano, strings, bass, drums" registration={register("instruments")} />
        <Field label="편곡 스타일" placeholder="예: gradual ballad build" registration={register("arrangement_style")} />
      </section>

      <section>
        <h2 className="mb-4 text-lg font-black text-zinc-50">참고하고 싶은 분석 곡</h2>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {songs.map((song) => (
            <SongCard key={song.id} song={song} selectable selected={selectedSongIds.includes(song.id)} onToggle={toggleSong} />
          ))}
        </div>
      </section>

      {error ? <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-100">{error}</div> : null}
      <button disabled={isSubmitting} className="focus-ring w-full rounded-lg bg-cyan-400 px-5 py-3 text-sm font-black text-zinc-950 disabled:bg-zinc-700 disabled:text-zinc-400">
        {isSubmitting ? "생성 중..." : "신곡 프로젝트 생성"}
      </button>
    </form>
  );
}

function Field({ label, placeholder, registration }: { label: string; placeholder: string; registration: UseFormRegisterReturn }) {
  return (
    <label className="block text-sm font-bold text-zinc-100">
      <span className="mb-2 block">{label}</span>
      <input {...registration} placeholder={placeholder} className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600" />
    </label>
  );
}
