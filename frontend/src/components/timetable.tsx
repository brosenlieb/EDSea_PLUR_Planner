// frontend/src/components/timetable.tsx
"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { EventSlot } from '../types';
import { getActivityLabel, formatTimeET, getFestivalDayInfo } from '../lib/utils';

interface TimetableProps {
  schedule: EventSlot[];
  loading: boolean;
  title?: string;
  showBackButton?: boolean;
  onBack?: () => void;
  backHref?: string;
  shareUrl?: string;
  onCopyShare?: () => void;
  copied?: boolean;
}

export default function Timetable({
  schedule,
  loading,
  title = "Schedule",
  showBackButton = false,
  onBack,
  backHref,
  shareUrl,
  onCopyShare,
  copied = false,
}: TimetableProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (loading || !isMounted) {
    return (
      <div className="space-y-6">
        <h2 className="text-xl font-bold">{title}</h2>
        <div className="animate-pulse space-y-4 py-4">
          <div className="h-20 bg-gray-200 rounded-lg"></div>
          <div className="h-20 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        {showBackButton && (
          backHref ? (
            <Link href={backHref} className="text-gray-500 hover:text-black font-medium">
              ← Back
            </Link>
          ) : onBack ? (
            <button onClick={onBack} className="text-gray-500 hover:text-black font-medium">
              ← Back
            </button>
          ) : null
        )}
        <h2 className="text-xl font-bold">{title}</h2>
        {shareUrl && onCopyShare && (
          <button
            onClick={onCopyShare}
            disabled={copied}
            className={`px-4 py-2 rounded font-semibold text-sm flex items-center gap-2 transition-colors ${
              copied 
                ? 'bg-green-500 text-white' 
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {copied ? 'Copied!' : 'Share'}
          </button>
        )}
      </div>

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
          
          let gapMinutes = 0;
          let showFreeTimeBlock = false;

          if (nextSlot) {
            // Force ISO parse consistency across environments
            const parseIso = (str: string) => {
              if (!str) return 0;
              const hasOffset = str.includes("Z") || str.includes("+") || (str.includes("-") && str.length > 19);
              return new Date(hasOffset ? str : `${str}Z`).getTime();
            };

            const currentEndTime = parseIso(slot.end_time);
            const nextStartTime = parseIso(nextSlot.start_time);
            gapMinutes = Math.round((nextStartTime - currentEndTime) / 60000);
            
            const nextDateInfo = getFestivalDayInfo(nextSlot.start_time);

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
    </div>
  );
}