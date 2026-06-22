import { AnalyzeForm } from "@/components/analysis/AnalyzeForm";
import { GenreBestsellerImportPanel } from "@/components/research/GenreBestsellerImportPanel";

export default function AnalyzePage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">YouTube Reference Analysis</p>
        <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">레퍼런스곡 연구 프로필 만들기</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">
          YouTube 링크를 시작점으로 곡을 식별하고, 허용된 메타데이터와 공개 음악 데이터, 사용자가 입력한 가사/코드/메모를
          결합해 Reference Song Analysis 프로필을 만듭니다. 권한 있는 오디오 파일을 추가하면 별도 음악 정보 분석 모듈을
          통해 BPM, Key, chroma, loudness 같은 신호 기반 항목도 함께 저장할 수 있습니다.
        </p>
      </div>
      <GenreBestsellerImportPanel />
      <AnalyzeForm />
    </div>
  );
}
