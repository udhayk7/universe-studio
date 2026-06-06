import { ConsistencyDashboard } from "@/components/studio/consistency-dashboard";

type ConsistencyPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ConsistencyPage({ params }: ConsistencyPageProps) {
  const { id } = await params;

  return <ConsistencyDashboard universeId={id} />;
}
