import { PatternLabClient } from "@/components/patterns/PatternLabClient";

export default function PatternsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">Pattern Lab</p>
        <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">공통 패턴과 성공 요소 분석</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">
          여러 곡의 분석 데이터를 묶어 장르, BPM, Key, 코드 진행, 후크, 곡 구조, 편곡, 보컬 처리, 히트 포인트의 공통 경향을 찾습니다.
          결과는 기존 곡 복제가 아니라 새 곡에 적용할 창작 원리로 일반화됩니다.
        </p>
      </div>
      <PatternLabClient />
    </div>
  );
}
