import { RecommendedArtist, ActivityPref, EventSlot } from '../types';

export interface ScheduleResponse {
  slug: string;
  events: EventSlot[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export const api = {
  getArtists: async () => {
    const res = await fetch(`${API_BASE}/artists`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  },

  getRecommendations: async (favorite_artist_ids: (string | number)[]): Promise<RecommendedArtist[]> => {
    const parsedIds = favorite_artist_ids.map((id) => typeof id === 'string' ? parseInt(id, 10) : id);
    
    const res = await fetch(`${API_BASE}/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ favorite_artist_ids: parsedIds })
    });
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
  },

  getActivities: async () => {
    const res = await fetch(`${API_BASE}/activities`);
    if (!res.ok) throw new Error(`Activities fetch error: ${res.status}`);
    return res.json();
  },

  generateSchedule: async (
    favorite_artist_ids: (string | number)[],
    activity_preferences: ActivityPref[]
  ): Promise<ScheduleResponse> => {
    const parsedArtistIds = favorite_artist_ids.map((id) => 
      typeof id === 'number' ? id : parseInt(id, 10)
    );
    
    const res = await fetch(`${API_BASE}/schedule/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        favorite_artist_ids: parsedArtistIds,
        activity_preferences: activity_preferences
      }),
    });
    if (!res.ok) throw new Error(`Failed to generate schedule: ${res.status}`);
    return res.json();
  },

  getScheduleBySlug: async (slug: string): Promise<ScheduleResponse> => {
    const res = await fetch(`${API_BASE}/schedule/${slug}`);
    if (!res.ok) throw new Error(`Failed to fetch schedule for slug: ${slug}`);
    return res.json();
  }
};