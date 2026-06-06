import { EpisodeGeneration } from "@/components/studio/episode-generation";

type NewEpisodePageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function NewEpisodePage({ params }: NewEpisodePageProps) {
  const { id } = await params;

  return <EpisodeGeneration universeId={id} />;
}
