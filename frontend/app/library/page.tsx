import { LibraryClient } from "@/components/library/LibraryClient";

export default function LibraryPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">Song Library</p>
        <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">분석 데이터 저장소</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">
          장르, BPM, Key, 후크 유형, 감정 키워드를 축적해 Pattern Lab과 Composer Coach의 재료로 사용합니다.
        </p>
      </div>
      <LibraryClient />
    </div>
  );
}
