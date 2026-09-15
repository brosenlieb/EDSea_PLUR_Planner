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

export interface Activity {
  id: number;
  activity_name: string;
  location_id: number;
  start_time: string;
  end_time: string;
}

export interface ActivityPref {
  activity_id: number;
  priority: 'must_have' | 'nice_to_have';
}

export interface EventSlot {
  id: string;
  title: string;
  event_type: 'performance' | 'activity';
  start_time: string;
  end_time: string;
  location_id: number;
  location_name: string;
  stage_name?: string;
  
  // Optional depending on event_type
  artist_ids?: number[];
  category?: string;
  priority?: 'must_have' | 'nice_to_have';
}