"use client";

import { create } from "zustand";

export type CreateInputMode = "idea" | "script" | "scene";

type StudioState = {
  sidebarCollapsed: boolean;
  createInputMode: CreateInputMode;
  activeUniverseId: string | null;
  setSidebarCollapsed: (value: boolean) => void;
  setCreateInputMode: (mode: CreateInputMode) => void;
  setActiveUniverseId: (id: string | null) => void;
};

export const useStudioStore = create<StudioState>((set) => ({
  sidebarCollapsed: false,
  createInputMode: "idea",
  activeUniverseId: null,
  setSidebarCollapsed: (value) => set({ sidebarCollapsed: value }),
  setCreateInputMode: (mode) => set({ createInputMode: mode }),
  setActiveUniverseId: (id) => set({ activeUniverseId: id }),
}));
