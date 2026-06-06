import { UniverseMemoryExplorer } from "@/components/studio/universe-memory-explorer";

type UniverseMemoryPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function UniverseMemoryPage({ params }: UniverseMemoryPageProps) {
  const { id } = await params;

  return <UniverseMemoryExplorer universeId={id} />;
}
