"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Artist, RecommendedArtist, PerformanceSlot } from "../types";

export default function FestivalPlanner() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [favorites, setFavorites] = useState<string[]>([]);

  return (
    <main className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-50 text-gray-900">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight">EDSea PLUR Planner 2026</h1>
        <p className="text-gray-500 mt-2">Pick your top artists, and we'll give you an EDMmaxxed Schedule.</p>
      </header>

      {step === 1 && (
        <ArtistSelection 
          favorites={favorites} 
          setFavorites={setFavorites} 
          onNext={() => setStep(2)} 
        />
      )}
      
      {step === 2 && (
        <RecommendationGrid 
          favorites={favorites} 
          onNext={() => setStep(3)} 
          onBack={() => setStep(1)} 
        />
      )}
      
      {step === 3 && (
        <Timetable 
          favorites={favorites} 
          onBack={() => setStep(2)} 
        />
      )}
    </main>
  );
}

// Artist Selection
function ArtistSelection({ favorites, setFavorites, onNext }: any) {
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
function RecommendationGrid({ favorites, onNext, onBack }: any) {
  const [recs, setRecs] = useState<RecommendedArtist[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecommendations(favorites)
      .then(setRecs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [favorites]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="text-gray-500 hover:text-black font-medium">← Back</button>
        <button onClick={onNext} className="bg-green-600 text-white px-6 py-2 rounded font-semibold">
          Build My Schedule
        </button>
      </div>
      
      <div>
        <h2 className="text-xl font-bold">2. Your AI Matches</h2>
        <p className="text-gray-600">Based on your selections, we've added these artists to your schedule pool.</p>
      </div>

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
function Timetable({ favorites, onBack }: any) {
  const [schedule, setSchedule] = useState<PerformanceSlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.generateSchedule(favorites)
      .then(setSchedule)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [favorites]);

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <button onClick={onBack} className="text-gray-500 hover:text-black font-medium">← Back</button>
        <h2 className="text-xl font-bold">3. Your Optimized Schedule</h2>
      </div>

      {loading ? (
        <p className="text-center py-10 animate-pulse">Solving constraints & travel matrix...</p>
      ) : (
        <div className="space-y-4">
          {schedule.map((slot, index) => (
            <div key={slot.id} className="flex bg-white rounded border shadow-sm overflow-hidden">
              <div className="bg-slate-800 text-white p-4 w-32 flex flex-col justify-center items-center shrink-0">
                <span className="font-bold">{formatTime(slot.start_time)}</span>
                <span className="text-xs text-slate-300">to {formatTime(slot.end_time)}</span>
              </div>
              <div className="p-4 flex-grow">
                <h3 className="font-bold text-lg">{slot.artist_name}</h3>
                <p className="text-gray-600">{slot.stage_name} • <span className="text-sm font-medium">{slot.location}</span></p>
                {index < schedule.length - 1 && (
                  <p className="text-xs text-amber-600 mt-2 font-medium">
                    Next up: Travel to {schedule[index + 1].location}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}