import { CopyrightNotice } from "@/components/CopyrightNotice";
import { DashboardClient } from "@/components/dashboard/DashboardClient";

const FLOW = ["히트곡 수집", "상세 분석", "DB 저장", "통계 분석", "공통 패턴 추출", "내 노래 설계"];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <section className="grid items-end gap-6 lg:grid-cols-[1fr_0.72fr]">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.28em] text-cyan-300">Hit Song Lab</p>
          <h1 className="mt-3 max-w-5xl text-4xl font-black leading-tight text-zinc-50 sm:text-6xl">
            히트곡의 창작 원리를 데이터로 축적하고, 통계화해 새 노래를 설계합니다.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-zinc-300">
            YouTube Reference Analysis로 레퍼런스곡을 빠르게 등록하고, Chord and Structure Analysis, Producer Research Mode,
            Hit Song Research Mode를 통해 장르별 패턴을 쌓아가는 대화형 AI 작곡 연구소입니다.
          </p>
        </div>
        <CopyrightNotice />
      </section>

      <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        {FLOW.map((item, index) => (
          <div key={item} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="text-xs font-black text-cyan-300">{index + 1}</p>
            <p className="mt-2 text-sm font-black text-zinc-50">{item}</p>
          </div>
        ))}
      </section>

      <DashboardClient />
    </div>
  );
}
