import { UniverseDetail } from "@/components/studio/universe-detail";

type UniverseDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function UniverseDetailPage({ params }: UniverseDetailPageProps) {
  const { id } = await params;

  return <UniverseDetail id={id} />;
}
