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

export interface EventSlot {
  id: number;
  title: string;
  event_type: 'performance' | 'activity';
  stage_name: string;
  location: string;
  start_time: string;
  end_time: string;
  artist_id?: number;
  artist_name?: string;
  category?: string;
}

export interface Activity {
  id: number;
  title: string;
  category: string;
  description?: string;
}

export interface ActivityPref {
  activity_id: number;
  priority: 'must_have' | 'nice_to_have';
}