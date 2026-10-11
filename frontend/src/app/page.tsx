"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { getActivityLabel, formatTimeET, getFestivalDayInfo } from "../lib/utils";
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
        const artistList = Array.isArray(data) 
          ? data 
          : data?.artists || data?.items || [];

        setArtists(artistList);
      })
      .catch((err) => {
        console.error("--> API ERROR:", err);
        setArtists([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const toggleArtist = (artistId: string) => {
    setFavorites((prev: string[]) => {
      if (prev.includes(artistId)) {
        return prev.filter((id) => id !== artistId);
      }
      // Raised cap from 5 to 10
      if (prev.length < 10) {
        return [...prev, artistId];
      }
      return prev;
    });
  };

  const isSelectionValid = favorites.length >= 3 && favorites.length <= 10;
  const isMaxReached = favorites.length >= 10;

  if (loading) return <p className="p-4 text-center">Loading artists...</p>;

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Select 3 to 10 Favorite Artists</h2>
        <span className={`text-sm font-semibold ${isSelectionValid ? 'text-green-400' : 'text-amber-400'}`}>
          Selected: {favorites.length} / 10 (Min 3)
        </span>
      </div>

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
              <span className="font-medium text-sm select-none text-white">{artist.name}</span>
            </label>
          );
        })}
      </div>

      <ActivitySelection 
        activityPrefs={activityPrefs} 
        setActivityPrefs={setActivityPrefs} 
      />

      <div className="flex justify-between items-center mt-6">
        <p className="text-sm">Selected: {favorites.length} / 10 (Minimum 3)</p>
        <button
          disabled={!isSelectionValid}
          onClick={onNext}
          className="px-6 py-2 bg-blue-600 rounded disabled:opacity-50 text-white font-semibold"
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
  favorites: string[]; activityPrefs: ActivityPref[]; onBack: () => void
}) {
  const [schedule, setSchedule] = useState<EventSlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.generateSchedule(favorites, activityPrefs)
      .then(setSchedule)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [favorites, activityPrefs]);

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
          {schedule.map((slot: EventSlot, index: number) => {
            const isPerformance = slot.event_type === "performance";
            const isAnnouncement = slot.category === "announcement";

            let cardStyle = "bg-white border-gray-200";
            let sidebarStyle = "bg-slate-800 text-white";
            let badgeStyle = "bg-blue-100 text-blue-800";
            let badgeText = "Music Set";

            if (isAnnouncement) {
              cardStyle = "bg-amber-50 border-amber-200";
              sidebarStyle = "bg-amber-800 text-amber-100";
              badgeStyle = "bg-amber-200 text-amber-900";
              badgeText = "Announcement";
            } else if (!isPerformance) {
              cardStyle = "bg-emerald-50 border-emerald-200";
              sidebarStyle = "bg-emerald-800 text-emerald-100";
              badgeStyle = "bg-emerald-200 text-emerald-800";
              badgeText = slot.category || "Activity";
            }

            const dateInfo = getFestivalDayInfo(slot.start_time);
            const isNewDay = index === 0 || getFestivalDayInfo(schedule[index - 1].start_time).rawDate !== dateInfo.rawDate;

            const nextSlot = index < schedule.length - 1 ? schedule[index + 1] : null;
            const isNextAnnouncement = nextSlot && nextSlot.category === "announcement";
            const isNextLocationNonActionable = nextSlot && (
              !nextSlot.location_name ||
              nextSlot.location_name === "All" ||
              nextSlot.location_name === "All Locations" ||
              nextSlot.location_name === "Shipwide / Informational"
            );
            
            // Only show "Next up: Travel" if there isn't a massive gap
            let gapMinutes = 0;
            let showFreeTimeBlock = false;

            if (nextSlot) {
              const currentEndTime = new Date(slot.end_time).getTime();
              const nextStartTime = new Date(nextSlot.start_time).getTime();
              gapMinutes = Math.round((nextStartTime - currentEndTime) / 60000);
              
              const nextDateInfo = getFestivalDayInfo(nextSlot.start_time);

              // Inject a Free Time block if the gap is >= 30 mins AND it's on the same festival day
              if (gapMinutes >= 30 && dateInfo.rawDate === nextDateInfo.rawDate) {
                showFreeTimeBlock = true;
              }
            }

            const showTravelLine = nextSlot && !isNextAnnouncement && !isNextLocationNonActionable && !showFreeTimeBlock;

            return (
              <div key={slot.id || index}>
                {isNewDay && (
                  <div className="pt-6 pb-2 border-b-2 border-indigo-500 mb-4 flex items-center justify-between">
                    <h3 className="text-xl font-extrabold text-indigo-900">
                      Day {dateInfo.dayNum} — {dateInfo.label}
                    </h3>
                  </div>
                )}

                <div className={`flex rounded-lg border shadow-sm overflow-hidden mb-3 ${cardStyle}`}>
                  <div className={`p-4 w-36 flex flex-col justify-center items-center shrink-0 ${sidebarStyle}`}>
                    <span className="font-bold text-sm">{formatTimeET(slot.start_time)}</span>
                    <span className="text-xs opacity-75">to {formatTimeET(slot.end_time)}</span>
                  </div>

                  <div className="p-4 flex-grow flex justify-between items-center">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-bold text-lg text-gray-900">
                          {slot.title}
                        </h3>
                        <span className={`text-xs px-2 py-0.5 rounded font-semibold ${badgeStyle}`}>
                          {badgeText}
                        </span>
                      </div>

                      <p className="text-sm text-gray-600">
                        {slot.stage_name && slot.stage_name !== "n/a" ? `${slot.stage_name} • ` : ""}
                        <span className="font-medium">{slot.location_name}</span>
                      </p>

                      {showTravelLine && (
                        <p className="text-xs text-amber-600 mt-2 font-medium">
                          Next up: Travel to {nextSlot.location_name}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Injected Free Time Block */}
                {showFreeTimeBlock && (
                  <div className="flex rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 mb-3 overflow-hidden opacity-80">
                    <div className="p-4 w-36 flex flex-col justify-center items-center shrink-0 text-gray-500">
                      <span className="font-bold text-sm">{formatTimeET(slot.end_time)}</span>
                      <span className="text-xs">to {formatTimeET(nextSlot!.start_time)}</span>
                    </div>
                    <div className="p-4 flex-grow flex items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 font-semibold italic">Free Time</span>
                        <span className="text-xs font-medium bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                          {gapMinutes >= 60 
                            ? `${Math.floor(gapMinutes / 60)} hr ${gapMinutes % 60} min` 
                            : `${gapMinutes} min`}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Activity Selection (Unrestricted selection)
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
      .then((data: Activity[] | { activities: Activity[] }) => {
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
        <h3 className="text-xl font-bold text-gray-900">Other Scheduled Activities</h3>
        <p className="text-sm text-gray-600">
          Yoga, gameshows, morning cartoons, and more can all be added to your PLUR planner!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {activities.map((activity) => {
          const currentPref = activityPrefs.find((p) => p.activity_id === activity.id);
          const currentPrefValue = currentPref ? currentPref.priority : "none";

          return (
            <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg bg-white shadow-sm mb-2">
              <span className="text-sm font-medium text-gray-900 pr-4">
                {getActivityLabel(activity)}
              </span>

              <select
                value={currentPrefValue}
                onChange={(e) => handlePriorityChange(activity.id, e.target.value)}
                className="text-xs border border-gray-300 rounded-md px-2.5 py-1.5 bg-gray-50 text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 flex-shrink-0"
              >
                <option value="none">Not Interested</option>
                <option value="nice_to_have">Nice to Have (if free)</option>
                <option value="must_have">Must Have (high priority)</option>
              </select>
            </div>
          );
        })}
      </div>
    </div>
  );
}