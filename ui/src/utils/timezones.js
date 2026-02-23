/***
 * Copyright (2026) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

// Utilities to build a dynamic list of IANA time zones with UTC offsets
function supportedTimeZones() {
  if (typeof Intl !== 'undefined' && typeof Intl.supportedValuesOf === 'function') {
    try {
      const zones = Intl.supportedValuesOf('timeZone');
      if (Array.isArray(zones) && zones.length) return zones;
    } catch (_) { /* ignore */ }
  }
  // Minimal fallback: include UTC and the user's local zone if available
  const local = getLocalTimeZone();
  const set = new Set(["UTC"]);
  if (local) set.add(local);
  return Array.from(set);
}

// Get the user's local time zone or default to 'UTC'
export function getLocalTimeZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  } catch (_) {
    return 'UTC';
  }
}

// Get the UTC offset label for a given time zone, e.g. "UTC+05:30"
function getOffsetLabel(tz) {
  try {
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      timeZoneName: 'shortOffset',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });
    const parts = fmt.formatToParts(new Date());
    const tzName = parts.find(p => p.type === 'timeZoneName')?.value || '';
    // Normalize variants like GMT+5:30 or UTC+05:30
    const match = tzName.match(/([A-Z]{2,3})?\s*([+-]?\d{1,2}:?\d{2})/);
    if (match) {
      const raw = match[2].replace(/^(\d)/, '+$1');
      const withColon = raw.includes(':') ? raw : `${raw.padStart(3, '+0')}:00`;
      return `UTC${withColon}`;
    }
  } catch (_) { /* ignore */ }
  return 'UTC±00:00';
}

// Build a list of time zone options with offsets for UI dropdowns
export function buildTimeZoneOptions() {
  const zones = supportedTimeZones();
  const items = zones.map(z => {
    const group = z.includes('/') ? z.split('/')[0] : 'Other';
    const offset = getOffsetLabel(z);
    return { value: z, label: `${offset} — ${z}`, group, offset };
  });
  // Sort by offset string then by zone name
  items.sort((a, b) => a.offset.localeCompare(b.offset) || a.value.localeCompare(b.value));
  return items;
}
