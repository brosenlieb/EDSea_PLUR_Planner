"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Artist, RecommendedArtist, EventSlot, ActivityPref, Activity } from "../types";

export default function FestivalPlanner() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [activityPrefs, setActivityPrefs] = useState<ActivityPref[]>([]);

  return (
    <main className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-50 text-gray-900">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight">EDSea PLUR Planner 2026</h1>
        <p className="text-gray-500 mt-2">Pick your top artists, preferred activities, and we'll give you an EDMmaxxed Schedule.</p>
      </header>

      {step === 1 && (
        <ArtistSelection 
          favorites={favorites} 
          setFavorites={setFavorites}
          activityPrefs={activityPrefs}
          setActivityPrefs={setActivityPrefs} 
          onNext={() => setStep(2)} 
        />
      )}
      
      {step === 2 && (
        <RecommendationGrid 
          favorites={favorites} 
          activityPrefs={activityPrefs}
          onNext={() => setStep(3)} 
          onBack={() => setStep(1)} 
        />
      )}
      
      {step === 3 && (
        <Timetable 
          favorites={favorites} 
          activityPrefs={activityPrefs}
          onBack={() => setStep(2)} 
        />
      )}
    </main>
  );
}

// Artist Selection
function ArtistSelection({ favorites, setFavorites, activityPrefs, setActivityPrefs, onNext }: any) {
    const [artists, setArtists] = useState<Artist[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
    api.getArtists()
        .then((data: any) => {
        
        // Handle array vs wrapped response shapes
        const artistList = Array.isArray(data) 
            ? data 
            : data?.artists || data?.items || [];

        setArtists(artistList);
        })
        .catch((err) => {
        console.error("--> API ERROR:", err);
        setArtists([]); // Reset to empty array on error
        })
        .finally(() => {
        setLoading(false);
        });
    }, []);

    const toggleArtist = (artistId: string) => {
    setFavorites((prev: string[]) => {
        if (prev.includes(artistId)) {
        return prev.filter((id) => id !== artistId); // Deselect
        }
        if (prev.length < 5) {
        return [...prev, artistId]; // Select if under limit
        }
        return prev; // Cap at 5 max
    });
    };

    const isSelectionValid = favorites.length >= 3 && favorites.length <= 5;
    const isMaxReached = favorites.length >= 5;

    if (loading) return <p className="p-4 text-center">Loading artists...</p>;

    return (
        <div className="max-w-4xl mx-auto p-4">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Select 3 to 5 Favorite Artists</h2>
            <span className={`text-sm font-semibold ${isSelectionValid ? 'text-green-400' : 'text-amber-400'}`}>
            Selected: {favorites.length} / 5 (Min 3)
            </span>
        </div>

        {/* Scrollable grid container for ~40 items */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[60vh] overflow-y-auto p-2 border border-gray-700 rounded-lg">
            {artists.map((artist) => {
            const idStr = artist.id.toString();
            const isChecked = favorites.includes(idStr);
            const isDisabled = !isChecked && isMaxReached;

            return (
                <label
                key={artist.id}
                className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    isChecked
                    ? 'bg-indigo-950 border-indigo-500 text-white'
                    : isDisabled
                    ? 'bg-gray-900 border-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                }`}
                >
                <input
                    type="checkbox"
                    checked={isChecked}
                    disabled={isDisabled}
                    onChange={() => toggleArtist(artist.id.toString())}
                    className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500 cursor-pointer disabled:cursor-not-allowed"
                />
                <span className="font-medium text-sm select-none">{artist.name}</span>
                </label>
            );
            })}
        </div>

        <ActivitySelection 
          activityPrefs={activityPrefs} 
          setActivityPrefs={setActivityPrefs} 
        />

        {/* Progress & Next Step Trigger */}
        <div className="flex justify-between items-center mt-6">
            <p className="text-sm">Selected: {favorites.length} / 5 (Minimum 3)</p>
            <button
            disabled={!isSelectionValid}
            onClick={onNext}
            className="px-6 py-2 bg-blue-600 rounded disabled:opacity-50"
            >
            Get Recommendations
            </button>
        </div>
        </div>
    );
}

// Recommendation Grid
function RecommendationGrid({ favorites, activityPrefs, onNext, onBack }: {
  favorites: string[]; activityPrefs: ActivityPref[]; onNext: () => void; onBack: () => void;
  }) {
  const [recs, setRecs] = useState<RecommendedArtist[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecommendations(favorites)
      .then(setRecs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [favorites]);

  const mustHaveCount = activityPrefs.filter(a => a.priority === 'must_have').length;
  const niceToHaveCount = activityPrefs.filter(a => a.priority === 'nice_to_have').length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="text-gray-500 hover:text-black font-medium">← Back</button>
        <button onClick={onNext} className="bg-green-600 text-white px-6 py-2 rounded font-semibold">
          Build My Schedule
        </button>
      </div>
      
      <div>
        <h2 className="text-xl font-bold">Your AI-suggested Matches</h2>
        <p className="text-gray-600">Based on your selections, we've added these artists to your schedule, along with your chosen activities.</p>
        <p className="text-gray-600">Note that Nice-to-Have activities will always lose to Must-Have Activities and all musical performances.</p>
      </div>

      {/* Activity Summary Badge Bar */}
      {activityPrefs.length > 0 && (
        <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg flex items-center justify-between">
          <span className="text-sm font-semibold text-indigo-900">Queued Activities:</span>
          <div className="flex gap-2">
            <span className="text-xs font-bold bg-indigo-200 text-indigo-800 px-2.5 py-1 rounded-full">
              {mustHaveCount} Must-Have
            </span>
            <span className="text-xs font-bold bg-gray-200 text-gray-700 px-2.5 py-1 rounded-full">
              {niceToHaveCount} Nice-to-Have
            </span>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-center py-10 animate-pulse">Running vector math...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recs.map(artist => (
            <div key={artist.id} className="p-4 bg-white rounded border shadow-sm flex justify-between items-center">
              <div>
                <h3 className="font-bold">{artist.name}</h3>
                <p className="text-sm text-gray-500">{artist.genre}</p>
              </div>
              <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 rounded">Match</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Timetable View
function Timetable({ favorites, activityPrefs, onBack }: {
  favorites: string[]; activityPrefs: ActivityPref[]; onBack: () => void}) {
  const [schedule, setSchedule] = useState<EventSlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.generateSchedule(favorites, activityPrefs)
      .then(setSchedule)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [favorites, activityPrefs]);

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="text-gray-500 hover:text-black font-medium">← Back</button>
        <h2 className="text-xl font-bold">Your Optimized Schedule</h2>
      </div>

      {loading ? (
        <p className="text-center py-10 animate-pulse">Solving constraints & travel matrix...</p>
      ) : (
        <div className="space-y-4">
          {schedule.map((slot, index) => {
            const isPerformance = slot.event_type === "performance";

            return (
              <div 
                key={slot.id} 
                className={`flex rounded-lg border shadow-sm overflow-hidden ${
                  isPerformance ? "bg-white border-gray-200" : "bg-purple-50 border-purple-200"
                }`}
              >
                {/* Time Sidebar */}
                <div className={`p-4 w-32 flex flex-col justify-center items-center shrink-0 ${
                  isPerformance ? "bg-slate-800 text-white" : "bg-purple-900 text-purple-100"
                }`}>
                  <span className="font-bold text-sm">{formatTime(slot.start_time)}</span>
                  <span className="text-xs opacity-75">to {formatTime(slot.end_time)}</span>
                </div>

                {/* Event Details */}
                <div className="p-4 flex-grow flex justify-between items-center">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-bold text-lg text-gray-900">
                        {isPerformance ? slot.artist_name : slot.title}
                      </h3>
                      <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                        isPerformance 
                          ? "bg-blue-100 text-blue-800" 
                          : "bg-purple-200 text-purple-800"
                      }`}>
                        {isPerformance ? "Music Set" : slot.category || "Activity"}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600">
                      {slot.stage_name} • <span className="font-medium">{slot.location}</span>
                    </p>

                    {index < schedule.length - 1 && (
                      <p className="text-xs text-amber-600 mt-2 font-medium">
                        Next up: Travel to {schedule[index + 1].location}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ActivitySelection({
  activityPrefs,
  setActivityPrefs,
}: {
  activityPrefs: ActivityPref[];
  setActivityPrefs: React.Dispatch<React.SetStateAction<ActivityPref[]>>;
}) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getActivities()
      .then((data: any) => {
        const activityList = Array.isArray(data) ? data : data?.activities || [];
        setActivities(activityList);
      })
      .catch((err) => {
        console.error("--> API ERROR fetching activities:", err);
        setActivities([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const handlePriorityChange = (activityId: number, value: string) => {
    setActivityPrefs((prev) => {
      const existingIndex = prev.findIndex((p) => p.activity_id === activityId);

      if (value === "none") {
        return prev.filter((p) => p.activity_id !== activityId);
      }

      const updatedPref: ActivityPref = {
        activity_id: activityId,
        priority: value as "must_have" | "nice_to_have",
      };

      if (existingIndex >= 0) {
        const copy = [...prev];
        copy[existingIndex] = updatedPref;
        return copy;
      }

      return [...prev, updatedPref];
    });
  };

  if (loading) {
    return <p className="mt-8 text-sm text-gray-500 animate-pulse">Loading festival activities...</p>;
  }

  return (
    <div className="mt-8 border-t border-gray-200 pt-6">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">Enhance Your Schedule with Activities</h3>
        <p className="text-sm text-gray-600">
          Want yoga, food tastings, or pool parties? Mark your priority level for non-musical events.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {activities.map((act) => {
          const currentPref =
            activityPrefs.find((p) => p.activity_id === act.id)?.priority || "none";

          return (
            <div
              key={act.id}
              className="flex items-center justify-between p-3.5 border rounded-lg bg-white shadow-sm"
            >
              <div>
                <span className="font-semibold text-gray-900 block text-sm">{act.title}</span>
                <span className="text-xs font-bold text-purple-600 uppercase tracking-wide">
                  {act.category}
                </span>
              </div>

              <select
                value={currentPref}
                onChange={(e) => handlePriorityChange(act.id, e.target.value)}
                className="text-xs border border-gray-300 rounded-md px-2.5 py-1.5 bg-gray-50 text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="none">Not Interested</option>
                <option value="nice_to_have">Nice to Have (If free)</option>
                <option value="must_have">Must Have (High Priority)</option>
              </select>
            </div>
          );
        })}
      </div>
    </div>
  );
}