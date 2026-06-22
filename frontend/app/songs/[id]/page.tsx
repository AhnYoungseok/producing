import { SongDetailClient } from "@/components/analysis/SongDetailClient";

export default async function SongResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SongDetailClient id={id} />;
}
