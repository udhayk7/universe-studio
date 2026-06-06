import { SectionHeader } from "@/components/common/section-header";
import { CreateUniverseForm } from "@/components/studio/create-universe-form";

export default function CreateUniversePage() {
  return (
    <div className="mx-auto max-w-7xl">
      <SectionHeader
        eyebrow="Create"
        title="Begin with a premise, script, or scene."
        description="Give the studio enough signal to name the world, define its mood, and preserve its first premise."
      />
      <div className="mt-10">
        <CreateUniverseForm />
      </div>
    </div>
  );
}
