export function BarList({ title, items }: { title: string; items: Array<{ label: string; count: number }> }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <h2 className="text-base font-black text-zinc-50">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.length === 0 ? <p className="text-sm text-zinc-500">아직 데이터가 없습니다.</p> : null}
        {items.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="truncate text-zinc-300">{item.label}</span>
              <span className="font-bold text-zinc-100">{item.count}</span>
            </div>
            <div className="mt-1 h-2 rounded bg-zinc-800">
              <div className="h-2 rounded bg-cyan-400" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
