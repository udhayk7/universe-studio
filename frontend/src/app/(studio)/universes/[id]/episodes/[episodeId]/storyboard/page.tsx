import { StoryboardViewer } from "@/components/studio/storyboard-viewer";

type StoryboardPageProps = {
  params: Promise<{
    id: string;
    episodeId: string;
  }>;
};

export default async function StoryboardPage({ params }: StoryboardPageProps) {
  const { id, episodeId } = await params;

  return <StoryboardViewer universeId={id} episodeId={episodeId} />;
}
