import { Activity } from "@/types";

const FESTIVAL_START_DATE_STR = "2025-11-01";

/**
 * Formats ISO strings from the backend into 12-hour AM/PM Eastern strings.
 * e.g., "2025-11-01T16:30:00-04:00" -> "4:30 PM"
 */
export function formatTimeET(isoString: string): string {
  if (!isoString) return "";

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "";

  return date.toLocaleTimeString("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

/**
 * Calculates day grouping and labels for the timeline.
 * Late-night sets (12:00 AM – 5:59 AM ET) group with the previous day.
 */
export function getFestivalDayInfo(isoString: string) {
  if (!isoString) return { dayNum: 1, label: "Day 1", rawDate: "" };

  const eventDate = new Date(isoString);
  if (isNaN(eventDate.getTime())) return { dayNum: 1, label: "Day 1", rawDate: "" };

  // Convert to Eastern Date components
  const easternDateStr = eventDate.toLocaleDateString("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  const [m, d, y] = easternDateStr.split("/");
  const localEasternDate = new Date(`${y}-${m}-${d}T00:00:00`);

  const hoursET = parseInt(
    eventDate.toLocaleTimeString("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      hour12: false,
    }),
    10
  );

  // Late-night sets (12:00 AM - 5:59 AM ET) belong to previous day
  if (hoursET < 6) {
    localEasternDate.setDate(localEasternDate.getDate() - 1);
  }

  const formattedY = localEasternDate.getFullYear();
  const formattedM = String(localEasternDate.getMonth() + 1).padStart(2, "0");
  const formattedD = String(localEasternDate.getDate()).padStart(2, "0");
  const rawDate = `${formattedY}-${formattedM}-${formattedD}`;

  const startDate = new Date(`${FESTIVAL_START_DATE_STR}T00:00:00`);
  const diffTime = localEasternDate.getTime() - startDate.getTime();
  const dayNum = Math.round(diffTime / (1000 * 60 * 60 * 24)) + 1;
  const validDay = !isNaN(dayNum) && dayNum > 0 ? dayNum : 1;

  const label = localEasternDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  return { dayNum: validDay, label, rawDate };
}

/**
 * Returns activity label for selection dropdowns.
 */
export function getActivityLabel(activity: Activity): string {
  if (!activity || !activity.start_time) return activity?.activity_name || "";

  const dayInfo = getFestivalDayInfo(activity.start_time);
  const startTimeStr = formatTimeET(activity.start_time);
  const endTimeStr = formatTimeET(activity.end_time);

  if (!startTimeStr || !endTimeStr) {
    return activity.activity_name;
  }

  return `${activity.activity_name}, Day ${dayInfo.dayNum}, ${startTimeStr} - ${endTimeStr}`;
}