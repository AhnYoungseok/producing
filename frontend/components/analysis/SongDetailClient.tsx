"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";

import { JsonCard } from "@/components/analysis/JsonCard";
import { fetchSong, fetchSongAnalysis, updateSongResearchData } from "@/lib/api";
import type { ConfidenceValue, HitSongResearchProfile, ProducerReportSection, Song, SongAnalysis } from "@/types/domain";

const LEGACY_SECTION_LABELS: Array<[keyof SongAnalysis, string]> = [
  ["concept", "컨셉 원본 데이터"],
  ["lyrics", "가사 원본 데이터"],
  ["structure", "곡 구조 원본 데이터"],
  ["harmony", "코드/화성 원본 데이터"],
  ["melody", "멜로디 원본 데이터"],
  ["hook", "후크 원본 데이터"],
  ["rhythm", "리듬/그루브 원본 데이터"],
  ["arrangement", "편곡 원본 데이터"],
  ["vocal", "보컬 원본 데이터"],
  ["mixing", "믹싱 원본 데이터"],
  ["hit_factor", "히트 포인트 원본 데이터"],
  ["takeaway", "창작 적용 원본 데이터"]
];

const PRODUCER_ORDER = [
  "production_concept",
  "structure_energy",
  "harmony_design",
  "melody_hook",
  "lyrics_storytelling",
  "rhythm_groove",
  "arrangement_layering",
  "vocal_production",
  "sound_mixing",
  "hit_points",
  "creative_application",
  "data_confidence"
];

export function SongDetailClient({ id }: { id: string }) {
  const [song, setSong] = useState<Song | null>(null);
  const [analysis, setAnalysis] = useState<SongAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchSong(id), fetchSongAnalysis(id)])
      .then(([songData, analysisData]) => {
        setSong(songData);
        setAnalysis(analysisData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "분석 상세를 불러오지 못했습니다."));
  }, [id]);

  const producerSections = useMemo(() => extractProducerSections(analysis), [analysis]);

  if (error) {
    return <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-5 text-sm text-red-100">{error}</div>;
  }
  if (!song || !analysis) {
    return <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-300">불러오는 중...</div>;
  }

  const researchProfile = asResearchProfile(song.research_profile);
  const hasUploadedAudio = Boolean(song.file_name);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">
              {researchProfile ? "YouTube Reference Analysis" : "Producer Research Mode"}
            </p>
            <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">{song.title}</h1>
            <p className="mt-2 text-sm text-zinc-400">
              {song.artist || "아티스트 미상"} · {song.genre || "Unknown Genre"} · {song.country || "Unknown Country"}
            </p>
          </div>
          {song.youtube_url ? (
            <a href={song.youtube_url} target="_blank" rel="noreferrer" className="focus-ring rounded-lg border border-zinc-700 px-4 py-2 text-sm font-bold text-zinc-100">
              YouTube 레퍼런스 열기
            </a>
          ) : null}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.2fr)]">
          <YouTubeReferenceCard song={song} />
          <AnalysisSourceCard hasUploadedAudio={hasUploadedAudio} fileName={song.file_name} />
        </div>

        {researchProfile ? <ResearchProfileSummary profile={researchProfile} /> : null}
        {researchProfile ? <LyricsFullTextCard song={song} profile={researchProfile} /> : null}
        <AnalysisHighlights analysis={analysis} />
        {researchProfile ? (
          <ResearchDataEditor
            song={song}
            onUpdated={(nextSong, nextAnalysis) => {
              setSong(nextSong);
              setAnalysis(nextAnalysis);
            }}
          />
        ) : null}

        {hasUploadedAudio ? (
          <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label="BPM" value={analysis.audio_features.bpm.toFixed(1)} />
            <Metric label="Key" value={analysis.audio_features.estimated_key} />
            <Metric label="길이" value={`${analysis.audio_features.duration_seconds.toFixed(1)}s`} />
            <Metric label="Loudness" value={`${analysis.audio_features.loudness_estimate.toFixed(1)} dBFS`} />
            <Metric label="Onset" value={`${analysis.audio_features.onset_density.toFixed(2)} /s`} />
          </dl>
        ) : (
          <p className="mt-6 rounded-lg border border-amber-500/30 bg-amber-950/20 p-4 text-sm leading-6 text-amber-100">
            이 결과는 Reference Song Analysis 프로필입니다. BPM, Key, 코드, 구조 같은 음악 특징은 공개 음악 데이터, 사용자가
            입력한 정보, 프로듀서 관점 추론을 함께 사용하며 각 항목에는 Data Confidence가 표시됩니다.
          </p>
        )}
      </section>

      <ProducerReport sections={producerSections} summary={String(analysis.full_report["summary"] ?? "")} />

      <JsonCard title="전체 리포트 원본 JSON" data={analysis.full_report} />
      <section className="grid gap-4 lg:grid-cols-2">
        {LEGACY_SECTION_LABELS.map(([key, label]) => (
          <JsonCard key={String(key)} title={label} data={analysis[key] as Record<string, unknown>} />
        ))}
      </section>
    </div>
  );
}

function ResearchDataEditor({
  song,
  onUpdated
}: {
  song: Song;
  onUpdated: (song: Song, analysis: SongAnalysis) => void;
}) {
  const userInputs = asResearchProfile(song.research_profile)?.user_inputs ?? {};
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage("");
    const form = new FormData(event.currentTarget);
    try {
      const result = await updateSongResearchData(song.id, {
        lyrics_text: String(form.get("lyrics_text") ?? ""),
        chord_progression: String(form.get("chord_progression") ?? ""),
        analysis_notes: String(form.get("analysis_notes") ?? "")
      });
      onUpdated(result.song, result.analysis);
      setMessage("가사와 코드 진행 분석을 업데이트했습니다.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "분석 업데이트에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-6 rounded-lg border border-cyan-500/20 bg-zinc-950 p-4">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Research Data Update</p>
          <h2 className="mt-2 text-lg font-black text-zinc-50">가사·코드 진행 보강 분석</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            가사를 넣으면 핵심 말과 후크 후보를 찾고, 코드 진행을 넣으면 섹션별 화성 기능과 통계가 업데이트됩니다.
          </p>
        </div>
        <button disabled={isSaving} className="focus-ring rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-black text-zinc-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400">
          {isSaving ? "업데이트 중..." : "분석 업데이트"}
        </button>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <label className="block text-sm font-bold text-zinc-100">
          <span className="mb-2 block">가사 텍스트</span>
          <textarea
            name="lyrics_text"
            rows={8}
            defaultValue={String(userInputs["lyrics_text"] ?? "")}
            placeholder={"[Verse]\n...\n[Chorus]\n반복되는 핵심 문장"}
            className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600"
          />
        </label>
        <label className="block text-sm font-bold text-zinc-100">
          <span className="mb-2 block">코드 진행</span>
          <textarea
            name="chord_progression"
            rows={8}
            defaultValue={String(userInputs["chord_progression"] ?? "")}
            placeholder={"Verse: I - V - vi - IV\nPre-Chorus: ii - V - iii - vi\nChorus: IV - V - iii - vi\nBridge: ii - V/vi - vi"}
            className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600"
          />
        </label>
      </div>
      <label className="mt-4 block text-sm font-bold text-zinc-100">
        <span className="mb-2 block">프로듀서 메모</span>
        <textarea
          name="analysis_notes"
          rows={4}
          defaultValue={String(userInputs["analysis_notes"] ?? "")}
          placeholder="후렴 50초 진입, 마지막 후렴 애드리브, 피아노 중심 편곡 등"
          className="focus-ring w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600"
        />
      </label>
      {message ? <p className="mt-3 rounded border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm leading-6 text-zinc-200">{message}</p> : null}
    </form>
  );
}

function LyricsFullTextCard({ song, profile }: { song: Song; profile: HitSongResearchProfile }) {
  const lyricsText = String(profile.user_inputs?.lyrics_text ?? "").trim();
  const searchUrl = officialLyricsSearchUrl(song);

  return (
    <section className="mt-6 rounded-lg border border-violet-500/20 bg-zinc-950 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Lyrics Source</p>
          <h2 className="mt-2 text-lg font-black text-zinc-50">실제 가사 표시</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            자동 누적 데이터에는 저작권 보호 가사 전문을 저장하지 않습니다. 사용자가 직접 제공한 가사만 이 영역에 표시하고 분석합니다.
          </p>
        </div>
        <a href={searchUrl} target="_blank" rel="noreferrer" className="focus-ring rounded-lg border border-zinc-700 px-4 py-2 text-sm font-bold text-zinc-100">
          공식 가사 검색
        </a>
      </div>
      {lyricsText ? (
        <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-sm leading-7 text-zinc-100">
          {lyricsText}
        </pre>
      ) : (
        <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-950/20 p-4 text-sm leading-6 text-amber-100">
          이 곡에는 아직 사용자가 제공한 실제 가사가 없습니다. 아래 “가사·코드 진행 보강 분석”에 가사를 붙여 넣고 업데이트하면
          여기에서 실제 가사를 확인하고 핵심 말, 반복 문장, 후렴 후보를 분석할 수 있습니다.
        </div>
      )}
    </section>
  );
}

function AnalysisHighlights({ analysis }: { analysis: SongAnalysis }) {
  const lyrics = analysis.lyrics ?? {};
  const harmony = analysis.harmony ?? {};
  const keyPhrases = Array.isArray(lyrics["key_phrase_candidates"]) ? (lyrics["key_phrase_candidates"] as Array<Record<string, unknown>>) : [];
  const repeated = Array.isArray(lyrics["repeated_key_phrases"]) ? (lyrics["repeated_key_phrases"] as unknown[]) : [];

  return (
    <section className="mt-6 grid gap-4 lg:grid-cols-2">
      <article className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Lyric Research</p>
        <h2 className="mt-2 text-lg font-black text-zinc-50">핵심 말과 후크 후보</h2>
        <dl className="mt-4 grid gap-3">
          <HighlightRow label="핵심 문장" value={lyrics["core_message"]} />
          <HighlightRow label="가사 주제" value={lyrics["lyric_theme"]} />
          <HighlightRow label="제목 사용 위치" value={lyrics["title_usage"]} />
          <HighlightRow label="반복 문장" value={repeated.length ? repeated.join(", ") : null} />
        </dl>
        {keyPhrases.length ? (
          <div className="mt-4 border-t border-zinc-800 pt-4">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Key Phrase Candidates</p>
            <div className="mt-3 space-y-2">
              {keyPhrases.slice(0, 4).map((item, index) => (
                <div key={`${formatFeatureValue(item["line"])}-${index}`} className="rounded border border-zinc-800 bg-zinc-900 px-3 py-2">
                  <p className="text-sm font-bold text-cyan-100">{formatFeatureValue(item["line"])}</p>
                  <p className="mt-1 text-xs text-zinc-500">{formatFeatureValue(item["reasons"])}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </article>

      <article className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Chord and Structure Analysis</p>
        <h2 className="mt-2 text-lg font-black text-zinc-50">코드 진행 해석</h2>
        <dl className="mt-4 grid gap-3">
          <HighlightRow label="Key" value={harmony["key"]} />
          <HighlightRow label="Verse" value={harmony["verse_progression"]} />
          <HighlightRow label="Pre-Chorus" value={harmony["pre_chorus_progression"]} />
          <HighlightRow label="Chorus" value={harmony["chorus_progression"]} />
          <HighlightRow label="Bridge" value={harmony["bridge_progression"]} />
          <HighlightRow label="화성 해석" value={harmony["producer_interpretation"]} />
          <HighlightRow label="창작 적용" value={harmony["creative_principle"]} />
        </dl>
      </article>
    </section>
  );
}

function HighlightRow({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="grid gap-1 rounded border border-zinc-800 bg-zinc-900 px-3 py-2 sm:grid-cols-[7rem_minmax(0,1fr)]">
      <dt className="text-xs font-black text-zinc-500">{label}</dt>
      <dd className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-200">{formatFeatureValue(value)}</dd>
    </div>
  );
}

function ProducerReport({ sections, summary }: { sections: ProducerReportSection[]; summary: string }) {
  if (sections.length === 0) {
    return null;
  }
  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-violet-500/30 bg-zinc-900 p-5 shadow-2xl">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Producer Research Mode</p>
        <h2 className="mt-2 text-2xl font-black text-zinc-50">프로듀서 관점 세부 분석</h2>
        <p className="mt-3 text-sm leading-6 text-zinc-300">{summary}</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {sections.map((section) => (
          <ProducerSectionCard key={section.id} section={section} />
        ))}
      </div>
    </section>
  );
}

function ProducerSectionCard({ section }: { section: ProducerReportSection }) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <h3 className="text-lg font-black text-zinc-50">{section.title}</h3>
      <div className="mt-4 space-y-4">
        <ReportBlock label="관찰" value={section.observation} accent="text-cyan-200" />
        <ReportBlock label="해석" value={section.interpretation} accent="text-violet-200" />
        <ReportBlock label="창작 적용" value={section.creative_application} accent="text-emerald-200" />
        <div className="border-t border-zinc-800 pt-4">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">데이터 체크포인트</p>
          <div className="mt-3 grid gap-2">
            {Object.entries(section.data_points || {}).map(([key, value]) => (
              <div key={key} className="grid gap-1 rounded border border-zinc-800 bg-zinc-950 px-3 py-2 sm:grid-cols-[10rem_minmax(0,1fr)]">
                <p className="text-xs font-bold text-zinc-500">{key}</p>
                <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-200">{formatFeatureValue(value)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}

function ReportBlock({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div>
      <p className={`text-xs font-black uppercase tracking-[0.2em] ${accent}`}>{label}</p>
      <p className="mt-2 text-sm leading-6 text-zinc-300">{value}</p>
    </div>
  );
}

function AnalysisSourceCard({ hasUploadedAudio, fileName }: { hasUploadedAudio: boolean; fileName?: string | null }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Analysis Source</p>
      {hasUploadedAudio ? (
        <>
          <p className="mt-3 text-sm leading-6 text-zinc-300">
            신호 기반 BPM, Key, chroma, energy, loudness는 사용자가 추가한 권한 있는 오디오 파일에서 계산했습니다.
          </p>
          <p className="mt-2 break-all text-xs text-zinc-500">분석 파일: {fileName}</p>
        </>
      ) : (
        <p className="mt-3 text-sm leading-6 text-zinc-300">
          이 곡은 YouTube Reference Analysis 프로필입니다. 허용된 레퍼런스 메타데이터, 공개 음악 DB, 사용자 입력 정보,
          프로듀서 관점 추론을 조합해 곡 특징을 저장했습니다.
        </p>
      )}
      <p className="mt-3 text-xs leading-5 text-amber-200">
        향후 신호 분석은 `reference_audio_analysis`, `music_information_retrieval`, `chord_structure_analyzer` 같은 분리된
        모듈로 연결할 수 있게 설계되어 있습니다.
      </p>
    </div>
  );
}

function ResearchProfileSummary({ profile }: { profile: HitSongResearchProfile }) {
  const features = profile.musical_features ?? {};
  return (
    <section className="mt-6 space-y-4">
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">Research Summary</p>
        <p className="mt-3 text-sm leading-6 text-zinc-200">{profile.research_summary}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <ConfidenceCard title="BPM" field={features.bpm} />
        <ConfidenceCard title="Key" field={features.key} />
        <ConfidenceCard title="Mood Tags" field={features.mood_tags} />
        <ConfidenceCard title="Lyric Theme" field={features.lyric_theme} />
        <ConfidenceCard title="Hook Type" field={features.hook_type} />
        <ConfidenceCard title="Hit Factors" field={features.hit_factors} />
      </div>
    </section>
  );
}

function ConfidenceCard({ title, field }: { title: string; field?: ConfidenceValue<unknown> }) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-black text-zinc-50">{title}</h3>
        <span className={`rounded px-2 py-1 text-[11px] font-black uppercase ${confidenceClass(field?.confidence)}`}>{field?.confidence || "low"}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-300">{formatFeatureValue(field?.value)}</p>
      <p className="mt-2 text-xs leading-5 text-zinc-500">Source: {field?.source || "not available"}</p>
    </article>
  );
}

function YouTubeReferenceCard({ song }: { song: Song }) {
  const metadata = song.youtube_metadata ?? {};
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-violet-300">YouTube Reference Metadata</p>
      <div className="mt-4 flex flex-col gap-4 sm:flex-row">
        {metadata.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={metadata.thumbnail_url} alt="" className="aspect-video w-full rounded-lg border border-zinc-800 object-cover sm:w-48" />
        ) : null}
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-black text-zinc-50">{metadata.title || song.title}</h2>
          <p className="mt-1 text-sm text-zinc-400">{metadata.channel_name || song.artist || "채널 정보 없음"}</p>
          <div className="mt-3 grid gap-2 text-xs text-zinc-500 sm:grid-cols-2">
            <span>영상 길이: {metadata.duration || "수집 대기"}</span>
            <span>게시일: {metadata.published_date || "수집 대기"}</span>
            <span>조회수: {metadata.view_count || "수집 대기"}</span>
            <span>상태: {metadata.metadata_status || "partial"}</span>
          </div>
        </div>
      </div>
      {metadata.description ? <p className="mt-4 max-h-28 overflow-hidden text-sm leading-6 text-zinc-400">{metadata.description}</p> : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
      <dt className="text-xs font-bold uppercase tracking-wide text-zinc-500">{label}</dt>
      <dd className="mt-2 break-words text-xl font-black text-zinc-50">{value}</dd>
    </div>
  );
}

function extractProducerSections(analysis: SongAnalysis | null): ProducerReportSection[] {
  if (!analysis) return [];
  const rawSections = analysis.full_report["producer_sections"];
  if (!rawSections || typeof rawSections !== "object" || Array.isArray(rawSections)) return [];
  const sectionMap = rawSections as Record<string, ProducerReportSection>;
  const rawOrder = analysis.full_report["section_order"];
  const order = Array.isArray(rawOrder) ? (rawOrder as string[]) : PRODUCER_ORDER;
  return order.map((key) => sectionMap[key]).filter(Boolean);
}

function asResearchProfile(value: unknown): HitSongResearchProfile | null {
  if (!value || typeof value !== "object") return null;
  const maybeProfile = value as HitSongResearchProfile;
  return maybeProfile.profile_type ? maybeProfile : null;
}

function officialLyricsSearchUrl(song: Song): string {
  const query = `${song.artist || ""} ${song.title} official lyrics`;
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function confidenceClass(confidence?: string) {
  if (confidence === "high") return "bg-emerald-500/15 text-emerald-200";
  if (confidence === "medium") return "bg-cyan-500/15 text-cyan-200";
  return "bg-amber-500/15 text-amber-200";
}

function formatFeatureValue(value: unknown): string {
  if (value == null || value === "") return "데이터 없음";
  if (Array.isArray(value)) return value.length > 0 ? value.map((item) => formatFeatureValue(item)).join(", ") : "데이터 없음";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}
