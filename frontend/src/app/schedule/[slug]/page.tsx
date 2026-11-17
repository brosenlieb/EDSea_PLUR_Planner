// frontend/src/app/schedule/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { EventSlot } from '../../../types';
import Timetable from '../../../components/timetable';

interface Props {
  params: { slug: string };
}

export default async function SharedSchedulePage({ params }: Props) {
  const { slug } = await params;
  const API_BASE = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000/api/v1';
  
  let schedule: EventSlot[] = [];

  try {
    const res = await fetch(`${API_BASE}/schedule/${slug}`, {
      next: { revalidate: 3600 }
    });
    
    if (!res.ok) {
      notFound();
    }
    
    const data = await res.json();
    schedule = data.events;
  } catch (err) {
    return (
      <div className="max-w-4xl mx-auto p-6 min-h-screen bg-gray-50 text-gray-900">
        <header className="mb-8 border-b pb-4">
          <h1 className="text-3xl font-extrabold tracking-tight">Shared Schedule</h1>
        </header>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <p className="font-semibold">Failed to load shared schedule.</p>
        </div>
      </div>
    );
  }

  return (
    <Timetable
      schedule={schedule}
      loading={false}
      title="Shared Schedule"
      showBackButton={true}
      backHref="/"
    />
  );
}