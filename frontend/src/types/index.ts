export interface Artist {
  id: number;
  name: string;
  genre: string;
  description?: string;
}

export interface RecommendedArtist {
  id: number;
  name: string;
  genre: string;
}

export interface PerformanceSlot {
  id: number;
  artist_id: number;
  artist_name: string;
  stage_id: number;
  stage_name: string;
  location: string;
  start_time: string;
  end_time: string;
}