import Link from "next/link";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/analyze", label: "Analyze Song" },
  { href: "/library", label: "Song Library" },
  { href: "/hooks", label: "Hook Lab" },
  { href: "/patterns", label: "Pattern Lab" },
  { href: "/project/new", label: "New Project" }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-zinc-800 bg-zinc-950/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Link href="/" className="focus-ring rounded-lg">
            <p className="text-sm font-black uppercase tracking-[0.28em] text-cyan-300">Hit Song Lab</p>
            <p className="mt-1 text-xs text-zinc-500">히트곡 DB · 통계 분석기 · AI 작곡 코치</p>
          </Link>
          <nav className="flex flex-wrap gap-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="focus-ring rounded-lg border border-zinc-800 px-3 py-2 text-xs font-bold text-zinc-300 transition hover:border-cyan-400 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      <footer className="border-t border-zinc-900 px-4 py-6 text-center text-xs leading-5 text-zinc-500">
        Hit Song Lab은 히트곡의 창작 원리를 데이터로 축적하고 통계화하여, 사용자가 자신만의 새 노래를 설계하도록 돕는 대화형 AI 작곡 연구소입니다.
      </footer>
    </div>
  );
}
