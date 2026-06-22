import type { ChartDataset } from "@/types/domain";

export function ChartPanel({ dataset }: { dataset: ChartDataset }) {
  const max = Math.max(1, ...dataset.items.map((item) => item.count));

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-300">Chart</p>
          <h2 className="mt-2 text-base font-black text-zinc-50">{dataset.title}</h2>
        </div>
        <span className="rounded border border-zinc-700 px-2 py-1 text-[11px] font-bold uppercase text-zinc-400">{dataset.items.length} rows</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-400">{dataset.description}</p>
      <div className="mt-5 space-y-3">
        {dataset.items.length === 0 ? <p className="text-sm text-zinc-500">아직 데이터가 없습니다.</p> : null}
        {dataset.items.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="min-w-0 truncate text-zinc-300" title={item.label}>
                {item.label}
              </span>
              <span className="font-bold text-zinc-100">{item.count}</span>
            </div>
            <div className="mt-1 h-2 rounded bg-zinc-800">
              <div className="h-2 rounded bg-cyan-400" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      {dataset.insight ? <p className="mt-4 rounded border border-cyan-500/20 bg-cyan-950/20 px-3 py-2 text-xs leading-5 text-cyan-100">{dataset.insight}</p> : null}
    </section>
  );
}
