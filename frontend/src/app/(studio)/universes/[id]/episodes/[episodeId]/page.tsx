import { EpisodeViewer } from "@/components/studio/episode-viewer";

type EpisodePageProps = {
  params: Promise<{
    id: string;
    episodeId: string;
  }>;
};

export default async function EpisodePage({ params }: EpisodePageProps) {
  const { id, episodeId } = await params;

  return <EpisodeViewer universeId={id} episodeId={episodeId} />;
}
