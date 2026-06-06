import { CharacterDossier } from "@/components/studio/character-dossier";

type CharacterDossierPageProps = {
  params: Promise<{
    id: string;
    characterId: string;
  }>;
};

export default async function CharacterDossierPage({ params }: CharacterDossierPageProps) {
  const { id, characterId } = await params;

  return <CharacterDossier universeId={id} characterId={characterId} />;
}
