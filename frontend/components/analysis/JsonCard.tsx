export function JsonCard({ title, data }: { title: string; data: Record<string, unknown> }) {
  return (
    <article className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 shadow-2xl">
      <h2 className="text-base font-black text-zinc-50">{title}</h2>
      <div className="mt-4 space-y-3">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-3">
            <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">{key}</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-zinc-200">{formatValue(value)}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "object" ? JSON.stringify(item, null, 2) : String(item))).join("\n");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value ?? "-");
}
