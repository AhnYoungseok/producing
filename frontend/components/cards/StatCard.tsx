export function StatCard({ label, value, caption }: { label: string; value: string | number; caption?: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-3 break-words text-3xl font-black text-zinc-50">{value}</p>
      {caption ? <p className="mt-2 text-sm leading-5 text-zinc-400">{caption}</p> : null}
    </div>
  );
}
