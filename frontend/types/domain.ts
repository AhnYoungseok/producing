export type Song = {
  id: string;
  title: string;
  artist?: string | null;
  genre?: string | null;
  release_year?: number | null;
  country?: string | null;
  youtube_url?: string | null;
  youtube_metadata?: YouTubeMetadata | null;
  research_profile?: HitSongResearchProfile | Record<string, unknown> | null;
  file_name?: string | null;
  duration?: number | null;
  bpm?: number | null;
  key?: string | null;
  created_at: string;
  updated_at: string;
  analysis_complete: boolean;
};

export type YouTubeMetadata = {
  source?: string | null;
  url?: string | null;
  video_id?: string | null;
  title?: string | null;
  channel_name?: string | null;
  description?: string | null;
  thumbnail_url?: string | null;
  duration?: string | null;
  published_date?: string | null;
  view_count?: string | null;
  metadata_status?: string | null;
  policy?: string | null;
};

export type AudioFeatures = {
  bpm: number;
  estimated_key: string;
  duration_seconds: number;
  loudness_estimate: number;
  onset_density: number;
  spectral_centroid_mean: number;
  zero_crossing_rate_mean: number;
  chroma_summary: Record<string, number>;
};

export type SongAnalysis = {
  id: string;
  song_id: string;
  concept: Record<string, unknown>;
  lyrics: Record<string, unknown>;
  structure: Record<string, unknown>;
  harmony: Record<string, unknown>;
  melody: Record<string, unknown>;
  hook: Record<string, unknown>;
  rhythm: Record<string, unknown>;
  arrangement: Record<string, unknown>;
  vocal: Record<string, unknown>;
  mixing: Record<string, unknown>;
  hit_factor: Record<string, unknown>;
  takeaway: Record<string, unknown>;
  full_report: Record<string, unknown>;
  audio_features: AudioFeatures;
  created_at: string;
  updated_at: string;
};

export type HookSummaryRow = {
  id: string;
  title: string;
  artist: string;
  genre: string;
  created_at?: string | null;
  lyric_hook_cue: string;
  lyric_function: string;
  hook_type: string;
  hook_location: string;
  interval_pattern: string;
  rhythm_pattern: string;
  contour: string;
  lyrics_status: string;
  lyrics_url: string;
  why_it_works: string;
  confidence: string;
};

export type HookSummaryResponse = {
  total_count: number;
  usable_count: number;
  rows: HookSummaryRow[];
};

export type ProducerReportSection = {
  id: string;
  title: string;
  observation: string;
  interpretation: string;
  creative_application: string;
  data_points: Record<string, unknown>;
};

export type AnalyzeResponse = {
  song: Song;
  analysis: SongAnalysis;
};

export type ResearchResponse = {
  song: Song;
  analysis: SongAnalysis;
  research_profile: HitSongResearchProfile;
};

export type GenreBestsellerCatalogItem = {
  genre: string;
  song_count: number;
  source: string;
  note: string;
};

export type GenreBestsellerImportResponse = {
  genre: string;
  requested_limit: number;
  imported_count: number;
  created_count: number;
  reused_count: number;
  songs: Song[];
  ranking_basis: string;
  youtube_policy: string;
  genre_statistics: HitSongStatistics;
  library_statistics: HitSongStatistics;
};

export type NextReferenceBatchResponse = {
  requested_limit: number;
  imported_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  songs: Song[];
  total_after: number;
  low_confidence: string[];
  queue_remaining: number;
  library_statistics: HitSongStatistics;
  youtube_policy: string;
  message: string;
  export_manifest?: LibraryExportResponse;
};

export type AutoBatchStatus = {
  enabled: boolean;
  running: boolean;
  interval_seconds: number;
  batch_size: number;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_result?: {
    imported_count: number;
    created_count: number;
    total_after: number;
    queue_remaining: number;
    songs: Array<Pick<Song, "id" | "title" | "artist" | "genre">>;
    message?: string | null;
  } | null;
  last_error?: string | null;
};

export type BulkResearchSeedImportResponse = {
  requested_target_count: number;
  requested_batch_size: number;
  created_count: number;
  reused_count: number;
  bulk_seed_total: number;
  library_song_count: number;
  songs: Song[];
  ranking_basis: string;
  youtube_policy: string;
  library_statistics: HitSongStatistics;
};

export type ConfidenceValue<T> = {
  value: T;
  confidence: "high" | "medium" | "low" | string;
  source: string;
  notes?: string | null;
};

export type HitSongResearchProfile = {
  profile_type: string;
  safe_design_policy: Record<string, unknown>;
  youtube_metadata: YouTubeMetadata;
  external_sources: Record<string, unknown>;
  identification: Record<string, ConfidenceValue<unknown>>;
  musical_features: Record<string, ConfidenceValue<unknown>>;
  user_inputs: Record<string, unknown>;
  research_summary: string;
};

export type Pattern = {
  id: string;
  pattern_type: string;
  genre?: string | null;
  description: string;
  source_song_ids: string[];
  pattern_json: Record<string, unknown>;
  created_at: string;
};

export type Project = {
  id: string;
  title: string;
  target_genre?: string | null;
  target_mood?: string | null;
  target_listener?: string | null;
  reference_song_ids: string[];
  theme?: string | null;
  vocal_style?: string | null;
  bpm_range?: string | null;
  lyric_language?: string | null;
  instruments?: string | null;
  arrangement_style?: string | null;
  concept_json: Record<string, unknown>;
  lyrics_plan_json: Record<string, unknown>;
  harmony_plan_json: Record<string, unknown>;
  melody_plan_json: Record<string, unknown>;
  hook_plan_json: Record<string, unknown>;
  arrangement_plan_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Blueprint = {
  id: string;
  project_id: string;
  blueprint_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ComposerOption = {
  id: string;
  label: string;
  summary: string;
  blueprint_updates?: Record<string, unknown>;
};

export type ComposerMessage = {
  role: "user" | "assistant";
  content: string;
  stage?: number;
  stage_title?: string;
  created_at?: string;
};

export type ComposerState = {
  project: Project;
  blueprint: Blueprint;
};

export type ComposerChatResponse = {
  project_id: string;
  stage: number;
  stage_title: string;
  assistant_message: string;
  options: ComposerOption[];
  recommendations?: Record<string, unknown> | null;
  blueprint: Blueprint;
};

export type Dashboard = {
  song_count: number;
  genre_counts: Array<{ label: string; count: number }>;
  average_bpm: number;
  top_keys: Array<{ label: string; count: number }>;
  top_progressions: Array<{ label: string; count: number }>;
  top_structures: Array<{ label: string; count: number }>;
  hook_distribution: Array<{ label: string; count: number }>;
  recent_songs: Song[];
  active_projects: Project[];
  pattern_count: number;
};

export type HitSongStatistics = {
  summary: {
    song_count: number;
    analyzed_song_count: number;
    average_bpm: number;
    average_first_chorus_time?: number | null;
    title_in_chorus_ratio?: number;
  };
  by_genre: Array<{ label: string; count: number }>;
  by_country: Array<{ label: string; count: number }>;
  by_decade: Array<{ label: string; count: number }>;
  by_bpm_range: Array<{ label: string; count: number }>;
  bpm_distribution?: Array<{ label: string; count: number }>;
  by_mood: Array<{ label: string; count: number }>;
  average_bpm_by_genre: Array<{ label: string; average_bpm: number; count: number }>;
  top_keys: Array<{ label: string; count: number }>;
  top_verse_progressions?: Array<{ label: string; count: number }>;
  top_pre_chorus_progressions?: Array<{ label: string; count: number }>;
  top_chorus_progressions: Array<{ label: string; count: number }>;
  top_bridge_progressions?: Array<{ label: string; count: number }>;
  top_song_structures?: Array<{ label: string; count: number }>;
  top_structures?: Array<{ label: string; count: number }>;
  hook_type_distribution: Array<{ label: string; count: number }>;
  title_usage_distribution: Array<{ label: string; count: number }>;
  title_in_chorus_ratio?: number;
  chorus_peak_positions: Array<{ label: string; count: number }>;
  final_chorus_expansions: Array<{ label: string; count: number }>;
  top_final_chorus_expansions?: Array<{ label: string; count: number }>;
  arrangement_builds: Array<{ label: string; count: number }>;
  top_mood_keywords?: Array<{ label: string; count: number }>;
  top_lyric_themes?: Array<{ label: string; count: number }>;
  top_arrangement_features?: Array<{ label: string; count: number }>;
  top_vocal_treatments?: Array<{ label: string; count: number }>;
  top_hit_factors?: Array<{ label: string; count: number }>;
  top_transferable_principles?: Array<{ label: string; count: number }>;
  common_principles_top_10?: Array<{ label: string; count: number }>;
  chart_datasets?: Record<string, ChartDataset>;
  pattern_summaries?: PatternSummary[];
  feature_schema?: FeatureSchemaCategory[];
  composer_questions: Array<{ question: string; answer: string; creative_use: string }>;
};

export type ChartDataset = {
  id: string;
  title: string;
  description: string;
  type: "horizontal_bar" | string;
  items: Array<{ label: string; count: number }>;
  insight?: string;
};

export type PatternSummary = {
  id: string;
  title: string;
  summary: string;
  producer_takeaway: string;
  confidence: string;
};

export type FeatureSchemaCategory = {
  category: string;
  fields: string[];
};

export type LibraryExportResponse = {
  generated_at: string;
  export_root: string;
  total_songs: number;
  genre_count: number;
  files: string[];
  spreadsheet_note?: string;
};
