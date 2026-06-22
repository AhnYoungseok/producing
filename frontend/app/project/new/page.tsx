import { NewProjectForm } from "@/components/composer/NewProjectForm";

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.24em] text-cyan-300">New Song Project</p>
        <h1 className="mt-3 text-3xl font-black text-zinc-50 sm:text-5xl">새 노래 프로젝트 생성</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">
          참고곡을 고르고, 원하는 감정과 장르를 입력하면 Composer Coach에서 신곡 제작 설계도를 생성합니다.
        </p>
      </div>
      <NewProjectForm />
    </div>
  );
}
