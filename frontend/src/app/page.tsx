"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { Artist, RecommendedArtist, PerformanceSlot } from "../types";

export default function FestivalPlanner() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [favorites, setFavorites] = useState<number[]>([]);
  
  return (
    <main className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-50 text-gray-900">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight">Shipwrecked Festival AI</h1>
        <p className="text-gray-500 mt-2">Pick your top artists, and we'll handle the logistics.</p>
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

// --- STEP 1: Artist Selection ---
function ArtistSelection({ favorites, setFavorites, onNext }: any) {
  const [artists, setArtists] = useState<Artist[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getArtists(search).then(setArtists).catch(console.error);
  }, [search]);

  const toggleArtist = (id: number) => {
    setFavorites((prev: number[]) => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">1. Select 3-5 Artists You Love</h2>
        <button 
          onClick={onNext}
          disabled={favorites.length < 1}
          className="bg-blue-600 text-white px-6 py-2 rounded font-semibold disabled:opacity-50"
        >
          Get AI Recommendations
        </button>
      </div>

      <input 
        type="text" 
        placeholder="Search artists by name or genre..." 
        className="w-full p-3 border rounded shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artists.map(artist => (
          <div 
            key={artist.id}
            onClick={() => toggleArtist(artist.id)}
            className={`p-4 rounded border cursor-pointer transition-all ${
              favorites.includes(artist.id) ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500' : 'bg-white hover:shadow-md'
            }`}
          >
            <h3 className="font-bold">{artist.name}</h3>
            <span className="text-xs bg-gray-200 px-2 py-1 rounded text-gray-700">{artist.genre}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- STEP 2: Recommendation Grid ---
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

// --- STEP 3: Timetable View ---
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