"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch, type UseFormRegisterReturn } from "react-hook-form";

import { CopyrightNotice } from "@/components/CopyrightNotice";
import { analyzeSong, fetchYouTubeMetadata, researchYouTubeSong } from "@/lib/api";
import type { YouTubeMetadata } from "@/types/domain";

type AnalyzeFormValues = {
  title: string;
  artist: string;
  genre: string;
  release_year: string;
  country: string;
  youtube_url: string;
  lyrics_text: string;
  chord_progression: string;
  analysis_notes: string;
};

const MAX_FILE_BYTES = 50 * 1024 * 1024;
const RESEARCH_STEPS = ["YouTube 메타데이터 확인", "공개 음악 데이터 보강", "곡 특징 정리", "Data Confidence 부여", "DB 저장"];
const AUDIO_STEPS = ["레퍼런스 등록", "권한 오디오 파일 확인", "WAV 변환", "BPM/Key 신호 분석", "프로듀서 리포트 생성", "DB 저장"];

export function AnalyzeForm() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { register, handleSubmit, control } = useForm<AnalyzeFormValues>();
  const youtubeUrl = useWatch({ control, name: "youtube_url", defaultValue: "" }) ?? "";
  const [file, setFile] = useState<File | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isMetadataLoading, setIsMetadataLoading] = useState(false);
  const [metadataPreview, setMetadataPreview] = useState<YouTubeMetadata | null>(null);
  const [step, setStep] = useState(0);

  async function onLoadMetadata() {
    setError("");
    setMetadataPreview(null);
    if (!youtubeUrl.trim()) {
      setError("YouTube 레퍼런스 링크를 먼저 입력해 주세요.");
      return;
    }
    if (!isYouTubeUrl(youtubeUrl)) {
      setError("유효한 YouTube 링크를 입력해 주세요.");
      return;
    }
    setIsMetadataLoading(true);
    try {
      setMetadataPreview(await fetchYouTubeMetadata(youtubeUrl.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "YouTube 레퍼런스 정보를 가져오지 못했습니다.");
    } finally {
      setIsMetadataLoading(false);
    }
  }

  async function onSubmit(values: AnalyzeFormValues) {
    setError("");
    if (!values.youtube_url?.trim()) {
      setError("YouTube 레퍼런스 링크를 입력해 주세요.");
      return;
    }
    if (!isYouTubeUrl(values.youtube_url)) {
      setError("유효한 YouTube 링크를 입력해 주세요.");
      return;
    }
    if (!accepted) {
      setError("저작권 및 데이터 출처 정책을 확인해 주세요.");
      return;
    }
    if (file) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    setIsSubmitting(true);
    setStep(0);
    const steps = file ? AUDIO_STEPS : RESEARCH_STEPS;
    const timer = window.setInterval(() => setStep((current) => Math.min(current + 1, steps.length - 1)), 700);
    try {
      if (file) {
        const formData = new FormData();
        formData.append("audio_file", file);
        Object.entries(values).forEach(([key, value]) => {
          if (value?.trim()) {
            formData.append(key, value.trim());
          }
        });
        const response = await analyzeSong(formData);
        router.push(`/songs/${response.song.id}`);
      } else {
        const response = await researchYouTubeSong({
          youtube_url: values.youtube_url.trim(),
          title: optionalText(values.title),
          artist: optionalText(values.artist),
          genre: optionalText(values.genre),
          country: optionalText(values.country),
          release_year: optionalYear(values.release_year),
          lyrics_text: optionalText(values.lyrics_text),
          chord_progression: optionalText(values.chord_progression),
          analysis_notes: optionalText(values.analysis_notes)
        });
        router.push(`/songs/${response.song.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reference Song Analysis 프로필 생성 중 오류가 발생했습니다.");
    } finally {
      window.clearInterval(timer);
      setIsSubmitting(false);
    }
  }

  const activeSteps = file ? AUDIO_STEPS : RESEARCH_STEPS;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 px-4 py-3 text-sm leading-6 text-cyan-100">
        기본 흐름은 <strong>YouTube 링크 → Reference Song Analysis 프로필</strong>입니다. 링크로 곡을 식별하고, 공개
        메타데이터와 공개 음악 DB, 사용자가 입력한 가사/코드/메모를 결합해 BPM, Key, 코드 진행, 구조, 후크, 편곡, 보컬,
        믹싱, 히트 포인트를 데이터베이스에 축적합니다.
      </div>

      <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <Field label="YouTube 레퍼런스 링크" placeholder="https://www.youtube.com/watch?v=..." registration={register("youtube_url", { required: true })} required />
          <button
            type="button"
            onClick={onLoadMetadata}
            disabled={isMetadataLoading || !youtubeUrl.trim()}
            className="focus-ring rounded-lg border border-cyan-400/60 px-4 py-2.5 text-sm font-black text-cyan-100 transition hover:bg-cyan-400/10 disabled:cursor-not-allowed disabled:border-zinc-700 disabled:text-zinc-500"
          >
            {isMetadataLoading ? "확인 중..." : "Reference Metadata 확인"}
          </button>
        </div>
        <YouTubePreview metadata={metadataPreview} />
      </section>

      <section
        className="rounded-lg border border-dashed border-zinc-700 bg-zinc-950 px-4 py-8 text-center"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          setFile(event.dataTransfer.files?.[0] ?? null);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/mp4"
          className="sr-only"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button type="button" onClick={() => inputRef.current?.click()} className="focus-ring rounded-lg bg-violet px-5 py-3 text-sm font-bold text-white hover:bg-violet-500">
          선택 사항: 권한 있는 오디오 파일 추가
        </button>
        <p className="mt-3 text-sm text-zinc-400">파일을 추가하지 않아도 YouTube Reference Analysis 프로필을 만들 수 있습니다.</p>
        <p className="mt-1 text-xs text-zinc-500">MP3, WAV, M4A · 최대 50MB · 본인이 소유했거나 분석 권한이 있는 파일만</p>
        {file ? (
          <div className="mt-3">
            <p className="break-all text-sm font-bold text-cyan-200">{file.name}</p>
            <button type="button" onClick={() => setFile(null)} className="focus-ring mt-2 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs font-bold text-zinc-300">
              파일 제거
            </button>
          </div>
        ) : null}
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <Field label="곡 제목 힌트" placeholder="예: Late Night Echo" registration={register("title")} />
        <Field label="아티스트 힌트" placeholder="예: Artist Name" registration={register("artist")} />
        <Field label="장르 힌트" placeholder="예: K-pop Ballad" registration={register("genre")} />
        <Field label="발매 연도 힌트" placeholder="예: 2024" registration={register("release_year")} />
        <Field label="국가 힌트" placeholder="예: Korea" registration={register("country")} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TextArea label="사용자 제공 가사" placeholder="가사를 붙여 넣으면 lyric theme, title usage, hook type의 신뢰도가 올라갑니다." registration={register("lyrics_text")} />
        <TextArea label="사용자 제공 코드 진행" placeholder={"Verse: I - V - vi - IV\nChorus: IV - V - iii - vi"} registration={register("chord_progression")} />
      </div>
      <TextArea
        label="프로듀서 리서치 메모"
        placeholder="구조, 편곡, 보컬, 믹싱, 후크에 대한 메모를 입력하세요. 예: 74 BPM, A major, chorus starts around 50s."
        registration={register("analysis_notes")}
      />

      <CopyrightNotice />
      <label className="flex items-start gap-3 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-200">
        <input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} className="mt-1 h-4 w-4" />
        <span>
          이 앱은 레퍼런스곡의 창작 원리를 연구하고 일반화하기 위한 도구이며, 기존 곡의 멜로디·가사·식별 가능한 편곡을
          그대로 재사용하지 않는다는 점을 확인합니다.
        </span>
      </label>

      {isSubmitting ? (
        <ol className="grid gap-2 md:grid-cols-3">
          {activeSteps.map((label, index) => (
            <li key={label} className={`rounded-lg border px-3 py-2 text-sm font-bold ${index <= step ? "border-cyan-400 bg-cyan-400/10 text-cyan-100" : "border-zinc-800 text-zinc-500"}`}>
              {index + 1}. {label}
            </li>
          ))}
        </ol>
      ) : null}

      {error ? <div className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-100">{error}</div> : null}

      <button
        disabled={isSubmitting || !accepted || !youtubeUrl.trim()}
        className="focus-ring w-full rounded-lg bg-cyan-400 px-5 py-3 text-sm font-black text-zinc-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
      >
        {isSubmitting ? "처리 중..." : file ? "Reference Analysis + 권한 오디오 분석 실행" : "YouTube 링크로 Research Profile 만들기"}
      </button>
    </form>
  );
}

function YouTubePreview({ metadata }: { metadata: YouTubeMetadata | null }) {
  if (!metadata) {
    return (
      <p className="mt-3 text-xs leading-5 text-zinc-500">
        Reference Metadata 확인을 누르면 영상 제목, 채널명, 썸네일, 길이, 게시일 등 허용된 메타데이터만 미리 보여줍니다.
      </p>
    );
  }
  return (
    <div className="mt-4 flex flex-col gap-4 rounded-lg border border-zinc-800 bg-zinc-900 p-4 sm:flex-row">
      {metadata.thumbnail_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={metadata.thumbnail_url} alt="" className="aspect-video w-full rounded-lg border border-zinc-800 object-cover sm:w-48" />
      ) : null}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Reference Metadata</p>
        <h2 className="mt-2 text-lg font-black text-zinc-50">{metadata.title || "제목 수집 대기"}</h2>
        <p className="mt-1 text-sm text-zinc-400">{metadata.channel_name || "채널 정보 수집 대기"}</p>
        <div className="mt-3 grid gap-2 text-xs text-zinc-500 sm:grid-cols-2">
          <span>길이: {metadata.duration || "수집 대기"}</span>
          <span>게시일: {metadata.published_date || "수집 대기"}</span>
          <span>조회수: {metadata.view_count || "수집 대기"}</span>
          <span>상태: {metadata.metadata_status || "partial"}</span>
        </div>
      </div>
    </div>
  );
}

function Field({ label, placeholder, registration, required }: { label: string; placeholder: string; registration: UseFormRegisterReturn; required?: boolean }) {
  return (
    <label className="block text-sm font-bold text-zinc-100">
      <span className="mb-2 block">
        {label}
        {required ? <span className="ml-1 text-cyan-300">*</span> : null}
      </span>
      <input {...registration} placeholder={placeholder} className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600" />
    </label>
  );
}

function TextArea({ label, placeholder, registration }: { label: string; placeholder: string; registration: UseFormRegisterReturn }) {
  return (
    <label className="block text-sm font-bold text-zinc-100">
      <span className="mb-2 block">{label}</span>
      <textarea {...registration} rows={6} placeholder={placeholder} className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600" />
    </label>
  );
}

function validateFile(file: File): string {
  const name = file.name.toLowerCase();
  if (![".mp3", ".wav", ".m4a"].some((extension) => name.endsWith(extension))) {
    return "MP3, WAV, M4A 파일만 업로드할 수 있습니다.";
  }
  if (file.size > MAX_FILE_BYTES) {
    return "파일 크기는 50MB를 초과할 수 없습니다.";
  }
  return "";
}

function isYouTubeUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    return (url.protocol === "http:" || url.protocol === "https:") && (host === "youtube.com" || host.endsWith(".youtube.com") || host === "youtu.be" || host.endsWith(".youtu.be"));
  } catch {
    return false;
  }
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function optionalYear(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : null;
}
