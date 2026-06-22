import { ComposerCoachClient } from "@/components/composer/ComposerCoachClient";

export default async function ComposerPage({ params }: { params: Promise<{ project_id: string }> }) {
  const { project_id } = await params;
  return <ComposerCoachClient projectId={project_id} />;
}
