import { TimelineWorkbench } from "@/components/studio/timeline-workbench";

type TimelinePageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function TimelinePage({ params }: TimelinePageProps) {
  const { id } = await params;

  return <TimelineWorkbench universeId={id} />;
}
