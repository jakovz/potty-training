from supabase import create_client
from datetime import datetime, timedelta
from os import getenv
from dotenv import load_dotenv
from collections import defaultdict
from statistics import mean, median, stdev

load_dotenv()

SUPABASE_URL = getenv('SUPABASE_URL')
SUPABASE_KEY = getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_event(event_type, location, timestamp):
    try:
        return supabase.table('events').insert({
            'type': event_type,
            'location': location,
            'timestamp': timestamp.isoformat()
        }).execute()
    except Exception as e:
        print(f"Error inserting event: {e}")
        raise

def get_events_by_type(event_type):
    response = supabase.table('events')\
        .select('*')\
        .eq('type', event_type)\
        .order('timestamp', desc=False)\
        .execute()
    
    return [
        {
            'timestamp': datetime.fromisoformat(row['timestamp']),
            'location': row['location']
        }
        for row in response.data
    ]

def calculate_intervals(events):
    if len(events) < 2:
        return []
    
    return [
        (events[i+1]['timestamp'] - events[i]['timestamp']).total_seconds() / 3600.0
        for i in range(len(events)-1)
    ]

def get_daily_averages_by_type(event_type):
    events = get_events_by_type(event_type)
    daily_events = defaultdict(list)
    
    for i in range(len(events)-1):
        current_event = events[i]
        next_event = events[i+1]
        interval = (next_event['timestamp'] - current_event['timestamp']).total_seconds() / 3600.0
        date = current_event['timestamp'].date()
        daily_events[date.isoformat()].append(interval)
    
    return {
        date: round(mean(intervals), 1)
        for date, intervals in daily_events.items()
    }

def get_location_stats(events):
    location_counts = defaultdict(int)
    for event in events:
        location_counts[event['location']] += 1
    total = len(events)
    return {loc: round(count/total * 100, 1) for loc, count in location_counts.items()}

def get_time_of_day_distribution(events):
    morning = evening = night = 0
    for event in events:
        hour = event['timestamp'].hour
        if 5 <= hour < 12:
            morning += 1
        elif 12 <= hour < 18:
            evening += 1
        else:
            night += 1
    total = len(events)
    return {
        'morning': round(morning/total * 100, 1) if total else 0,
        'evening': round(evening/total * 100, 1) if total else 0,
        'night': round(night/total * 100, 1) if total else 0
    }

def get_statistics():
    stats = {}
    
    for event_type in ['Pee', 'Poo']:
        events = get_events_by_type(event_type)
        intervals = calculate_intervals(events)
        
        if intervals:
            stats[f'{event_type.lower()}_max'] = round(max(intervals), 1)
            stats[f'{event_type.lower()}_avg'] = round(mean(intervals), 1)
            stats[f'{event_type.lower()}_median'] = round(median(intervals), 1)
            stats[f'{event_type.lower()}_std'] = round(stdev(intervals), 1) if len(intervals) > 1 else 0
            stats[f'{event_type.lower()}_location'] = get_location_stats(events)
            stats[f'{event_type.lower()}_time_dist'] = get_time_of_day_distribution(events)
        else:
            stats[f'{event_type.lower()}_max'] = 0
            stats[f'{event_type.lower()}_avg'] = 0
            stats[f'{event_type.lower()}_median'] = 0
            stats[f'{event_type.lower()}_std'] = 0
            stats[f'{event_type.lower()}_location'] = {'Inside': 0, 'Outside': 0}
            stats[f'{event_type.lower()}_time_dist'] = {'morning': 0, 'evening': 0, 'night': 0}

    # Calculate daily averages for both types
    stats['daily_averages'] = {
        'pee': get_daily_averages_by_type('Pee'),
        'poo': get_daily_averages_by_type('Poo')
    }
    
    return stats 