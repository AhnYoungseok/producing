import type {
  AnalyzeResponse,
  AutoBatchStatus,
  Blueprint,
  ComposerChatResponse,
  ComposerState,
  Dashboard,
  GenreBestsellerCatalogItem,
  GenreBestsellerImportResponse,
  HitSongStatistics,
  HookSummaryResponse,
  LibraryExportResponse,
  NextReferenceBatchResponse,
  Pattern,
  Project,
  ResearchResponse,
  Song,
  SongAnalysis,
  YouTubeMetadata
} from "@/types/domain";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8100/api";

export async function fetchDashboard(): Promise<Dashboard> {
  return request<Dashboard>("/library/dashboard");
}

export async function fetchStatistics(): Promise<HitSongStatistics> {
  return request<HitSongStatistics>("/library/statistics");
}

export async function fetchHookSummaries(): Promise<HookSummaryResponse> {
  return request<HookSummaryResponse>("/library/hook-summaries");
}

export async function exportLibrary(): Promise<LibraryExportResponse> {
  return request<LibraryExportResponse>("/library/export", { method: "POST" });
}

export async function fetchSongs(params?: URLSearchParams): Promise<Song[]> {
  const suffix = params?.toString() ? `?${params.toString()}` : "";
  const response = await request<{ songs: Song[] }>(`/songs${suffix}`);
  return response.songs;
}

export async function fetchSong(id: string): Promise<Song> {
  return request<Song>(`/songs/${id}`);
}

export async function fetchSongAnalysis(id: string): Promise<SongAnalysis> {
  return request<SongAnalysis>(`/songs/${id}/analysis`);
}

export async function updateSongResearchData(
  id: string,
  payload: { lyrics_text?: string | null; chord_progression?: string | null; analysis_notes?: string | null }
): Promise<ResearchResponse> {
  return request<ResearchResponse>(`/songs/${id}/research-data`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function analyzeSong(formData: FormData): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/analyze", { method: "POST", body: formData });
}

export async function researchYouTubeSong(payload: Record<string, unknown>): Promise<ResearchResponse> {
  return request<ResearchResponse>("/research/youtube", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function fetchGenreBestsellerCatalog(): Promise<GenreBestsellerCatalogItem[]> {
  const response = await request<{ genres: GenreBestsellerCatalogItem[] }>("/research/genre-bestsellers");
  return response.genres;
}

export async function importGenreBestsellers(genre: string, limit = 10): Promise<GenreBestsellerImportResponse> {
  return request<GenreBestsellerImportResponse>("/research/genre-bestsellers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ genre, limit })
  });
}

export async function importNextReferenceBatch(limit = 10): Promise<NextReferenceBatchResponse> {
  return request<NextReferenceBatchResponse>("/research/next-reference-batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit })
  });
}

export async function fetchAutoBatchStatus(): Promise<AutoBatchStatus> {
  return request<AutoBatchStatus>("/research/auto-batch/status");
}

export async function runAutoBatchNow(limit = 10): Promise<NextReferenceBatchResponse> {
  return request<NextReferenceBatchResponse>("/research/auto-batch/run-now", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit })
  });
}

export async function fetchYouTubeMetadata(url: string): Promise<YouTubeMetadata> {
  const params = new URLSearchParams({ url });
  return request<YouTubeMetadata>(`/youtube/metadata?${params.toString()}`);
}

export async function extractPatterns(songIds: string[], patternTypes: string[]): Promise<Pattern[]> {
  return request<Pattern[]>("/patterns/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ song_ids: songIds, pattern_types: patternTypes })
  });
}

export async function fetchPatterns(): Promise<Pattern[]> {
  return request<Pattern[]>("/patterns");
}

export async function createProject(payload: Record<string, unknown>): Promise<Project> {
  return request<Project>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function fetchProjects(): Promise<Project[]> {
  return request<Project[]>("/projects");
}

export async function fetchProject(id: string): Promise<Project> {
  return request<Project>(`/projects/${id}`);
}

export async function createBlueprint(projectId: string): Promise<Blueprint> {
  return request<Blueprint>(`/projects/${projectId}/blueprint`, { method: "POST" });
}

export async function fetchBlueprint(projectId: string): Promise<Blueprint> {
  return request<Blueprint>(`/projects/${projectId}/blueprint`);
}

export async function fetchComposerState(projectId: string): Promise<ComposerState> {
  return request<ComposerState>(`/composer/${projectId}`);
}

export async function sendComposerMessage(
  projectId: string,
  payload: { message?: string | null; selected_option_id?: string | null }
): Promise<ComposerChatResponse> {
  return request<ComposerChatResponse>(`/composer/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init });
  if (response.ok) {
    return response.json() as Promise<T>;
  }
  let message = `요청 실패: ${response.status}`;
  try {
    const body = (await response.json()) as { detail?: string };
    if (body.detail) {
      message = body.detail;
    }
  } catch {
    message = response.statusText || message;
  }
  throw new Error(message);
}
