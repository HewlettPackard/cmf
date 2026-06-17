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
// alias mapping
const TIMEZONE_ALIASES = {
  "Africa/Asmera": "Africa/Asmara",
  "Africa/Timbuktu": "Africa/Abidjan",
  "America/Atka": "America/Adak",
  "America/Buenos_Aires": "America/Argentina/Buenos_Aires",
  "America/Catamarca": "America/Argentina/Catamarca",
  "America/ComodRivadavia": "America/Argentina/Catamarca",
  "America/Cordoba": "America/Argentina/Cordoba",
  "America/Jujuy": "America/Argentina/Jujuy",
  "America/Mendoza": "America/Argentina/Mendoza",
  "America/Coral_Harbour": "America/Atikokan",
  "America/Ensenada": "America/Tijuana",
  "America/Fort_Wayne": "America/Indiana/Indianapolis",
  "America/Indianapolis": "America/Indiana/Indianapolis",
  "America/Knox_IN": "America/Indiana/Knox",
  "America/Louisville": "America/Kentucky/Louisville",
  "America/Montreal": "America/Toronto",
  "America/Porto_Acre": "America/Rio_Branco",
  "America/Rosario": "America/Argentina/Cordoba",
  "America/Santa_Isabel": "America/Tijuana",
  "America/Shiprock": "America/Denver",
  "America/Virgin": "America/Port_of_Spain",
  "Asia/Calcutta": "Asia/Kolkata",
  "Asia/Chongqing": "Asia/Shanghai",
  "Asia/Chungking": "Asia/Shanghai",
  "Asia/Dacca": "Asia/Dhaka",
  "Asia/Harbin": "Asia/Shanghai",
  "Asia/Katmandu": "Asia/Kathmandu",
  "Asia/Macao": "Asia/Macau",
  "Asia/Rangoon": "Asia/Yangon",
  "Asia/Saigon": "Asia/Ho_Chi_Minh",
  "Asia/Tel_Aviv": "Asia/Jerusalem",
  "Asia/Thimbu": "Asia/Thimphu",
  "Asia/Ujung_Pandang": "Asia/Makassar",
  "Asia/Ulan_Bator": "Asia/Ulaanbaatar",
  "Atlantic/Faeroe": "Atlantic/Faroe",
  "Atlantic/Jan_Mayen": "Europe/Oslo",
  "Australia/ACT": "Australia/Sydney",
  "Australia/Canberra": "Australia/Sydney",
  "Australia/Currie": "Australia/Hobart",
  "Australia/LHI": "Australia/Lord_Howe",
  "Australia/North": "Australia/Darwin",
  "Australia/NSW": "Australia/Sydney",
  "Australia/Queensland": "Australia/Brisbane",
  "Australia/South": "Australia/Adelaide",
  "Australia/Tasmania": "Australia/Hobart",
  "Australia/Victoria": "Australia/Melbourne",
  "Australia/West": "Australia/Perth",
  "Australia/Yancowinna": "Australia/Broken_Hill",
  "Brazil/Acre": "America/Rio_Branco",
  "Brazil/DeNoronha": "America/Noronha",
  "Brazil/East": "America/Sao_Paulo",
  "Brazil/West": "America/Manaus",
  "Canada/Atlantic": "America/Halifax",
  "Canada/Central": "America/Winnipeg",
  "Canada/Eastern": "America/Toronto",
  "Canada/Mountain": "America/Edmonton",
  "Canada/Newfoundland": "America/St_Johns",
  "Canada/Pacific": "America/Vancouver",
  "Canada/Saskatchewan": "America/Regina",
  "Canada/Yukon": "America/Whitehorse",
  "Chile/Continental": "America/Santiago",
  "Chile/EasterIsland": "Pacific/Easter",
  "Cuba": "America/Havana",
  "Egypt": "Africa/Cairo",
  "Eire": "Europe/Dublin",
  "Etc/GMT+0": "Etc/GMT",
  "Etc/GMT-0": "Etc/GMT",
  "Etc/GMT0": "Etc/GMT",
  "Etc/Greenwich": "Etc/GMT",
  "Etc/UCT": "Etc/UTC",
  "Etc/Universal": "Etc/UTC",
  "Etc/Zulu": "Etc/UTC",
  "Europe/Belfast": "Europe/London",
  "Europe/Nicosia": "Asia/Nicosia",
  "Europe/Tiraspol": "Europe/Chisinau",
  "GB": "Europe/London",
  "GB-Eire": "Europe/London",
  "GMT": "Etc/GMT",
  "GMT+0": "Etc/GMT",
  "GMT-0": "Etc/GMT",
  "GMT0": "Etc/GMT",
  "Greenwich": "Etc/GMT",
  "Hongkong": "Asia/Hong_Kong",
  "Iceland": "Atlantic/Reykjavik",
  "Iran": "Asia/Tehran",
  "Israel": "Asia/Jerusalem",
  "Jamaica": "America/Jamaica",
  "Japan": "Asia/Tokyo",
  "Kwajalein": "Pacific/Kwajalein",
  "Libya": "Africa/Tripoli",
  "Mexico/BajaNorte": "America/Tijuana",
  "Mexico/BajaSur": "America/Mazatlan",
  "Mexico/General": "America/Mexico_City",
  "NZ": "Pacific/Auckland",
  "NZ-CHAT": "Pacific/Chatham",
  "Navajo": "America/Denver",
  "PRC": "Asia/Shanghai",
  "Pacific/Ponape": "Pacific/Pohnpei",
  "Pacific/Samoa": "Pacific/Pago_Pago",
  "Pacific/Truk": "Pacific/Chuuk",
  "Pacific/Yap": "Pacific/Chuuk",
  "Poland": "Europe/Warsaw",
  "Portugal": "Europe/Lisbon",
  "ROC": "Asia/Taipei",
  "ROK": "Asia/Seoul",
  "Singapore": "Asia/Singapore",
  "Turkey": "Europe/Istanbul",
  "UCT": "Etc/UTC",
  "US/Alaska": "America/Anchorage",
  "US/Aleutian": "America/Adak",
  "US/Arizona": "America/Phoenix",
  "US/Central": "America/Chicago",
  "US/East-Indiana": "America/Indiana/Indianapolis",
  "US/Eastern": "America/New_York",
  "US/Hawaii": "Pacific/Honolulu",
  "US/Indiana-Starke": "America/Indiana/Knox",
  "US/Michigan": "America/Detroit",
  "US/Mountain": "America/Denver",
  "US/Pacific": "America/Los_Angeles",
  "US/Samoa": "Pacific/Pago_Pago",
  "UTC": "Etc/UTC",
  "Universal": "Etc/UTC",
  "W-SU": "Europe/Moscow",
  "WET": "Europe/Lisbon",
  "Zulu": "Etc/UTC",
};

// Normalizing old or non-standard time zone names to their modern IANA equivalents
function normalizeTimeZone(tz) {
  // Input: tz (string)
  // Output: string
  // Description: Converts known legacy timezone aliases to canonical IANA names.
  // Step 1: Check whether tz exists in TIMEZONE_ALIASES map.
  // Step 2: Return mapped canonical timezone when alias exists.
  // Step 3: Return original value when no alias mapping is found.
  // Example: "Asia/Calcutta" becomes "Asia/Kolkata".
  return TIMEZONE_ALIASES[tz] || tz;
}

// Get a list of supported time zones from the environment, with a fallback if not available
function supportedTimeZones() {
  // Input: none
  // Output: string[]
  // Description: Returns supported timezone list from Intl API with a UTC/local fallback.
  // Step 1: Try Intl.supportedValuesOf("timeZone") when available.
  // Step 2: Use returned list if it is a non-empty array.
  // Step 3: On failure, fallback to ["UTC", detectedLocalTimezone].
  // Example: older runtime may return ["UTC", "Asia/Kolkata"].
  // Intl is a modern API that provides a list of supported time zones, but it may not be available in all environments
  if (typeof Intl !== 'undefined' && typeof Intl.supportedValuesOf === 'function') {
    try {
      // returns an array of all timezone identifiers that the browser supports.
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
  // Input: none
  // Output: string
  // Description: Detects browser timezone and normalizes legacy aliases.
  // Step 1: Read timezone from Intl.DateTimeFormat().resolvedOptions().timeZone.
  // Step 2: Normalize returned value using normalizeTimeZone.
  // Step 3: Return UTC if timezone detection fails.
  // Example: browser returns Asia/Calcutta -> function returns Asia/Kolkata.
  try {
    // Get user's browser timezone, fallback to UTC if unavailable
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    return normalizeTimeZone(tz);
  } catch (_) {
    return 'UTC';
  }
}

// Calculate the UTC offset in minutes for a given time zone and date (defaulting to now)
// For eg: Asia/Kolkata is UTC+05:30, which is 330 minutes from UTC.
function getOffsetMinutes(tz, date = new Date()) {
  // Input: tz (string), date (Date, optional)
  // Output: number (UTC offset in minutes)
  // Description: Computes timezone UTC offset by comparing converted and original timestamps.
  // Step 1: Format date in target timezone using Intl.DateTimeFormat.
  // Step 2: Extract numeric parts and reconstruct equivalent UTC timestamp.
  // Step 3: Subtract original timestamp and convert milliseconds to minutes.
  // Step 4: Normalize negative zero to zero and return result.
  // Example: UTC noon rendered in Asia/Kolkata gives +330 minutes.

  // Create a formatter that converts the given UTC date into the target timezone.
  // Example: UTC 12:00 → Asia/Kolkata becomes 17:30
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: tz,        // Convert time into "Asia/Kolkata"
    year: 'numeric',     // e.g. "2026"
    month: '2-digit',    // e.g. "04"
    day: '2-digit',      // e.g. "01"
    hour: '2-digit',     // e.g. "17" (5 PM in 24-hour format)
    minute: '2-digit',   // e.g. "30"
    second: '2-digit',   // e.g. "00"
    hour12: false,       // Use 24-hour format (no AM/PM)
    hourCycle: 'h23'     // Keep hours between 00–23
  });

  // Break the formatted date into parts (structured format)
  const parts = fmt.formatToParts(date);

  // Convert parts into a clean object
  // Example: { year: "2026", month: "04", day: "01", hour: "17", minute: "30", second: "00" }
  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== 'literal') // Remove separators like "/", ":", ","
      .map((part) => [part.type, part.value])    // Keep only useful data
  );

  // Now we create a UTC timestamp from the timezone-adjusted values
  // We treat "17:30" as if it is UTC time
  // Example: Date.UTC(2026, 3, 1, 17, 30, 0) → timestamp for 17:30 UTC
  const zonedUtcMs = Date.UTC(
    Number(values.year),         // 2026
    Number(values.month) - 1,    // JS months are 0-based → April = 3
    Number(values.day),          // 1
    Number(values.hour),         // 17
    Number(values.minute),       // 30
    Number(values.second)        // 0
  );

  // Original timestamp:
  // date.getTime() = 12:00 UTC
  // zonedUtcMs: 17:30 UTC (but actually represents Asia/Kolkata time)
  // Difference: 17:30 - 12:00 = 5 hours 30 minutes = 330 minutes
  const offset = Math.round(
    (zonedUtcMs - date.getTime()) / 60000 // Convert milliseconds → minutes
  );

  // Handle edge case: avoid returning -0
  // If offset is 0 or -0 → return clean 0
  return offset === 0 ? 0 : offset;
}

// Format the offset in minutes into a human-readable string like "UTC+05:30" or "UTC-04:00"
function formatOffsetLabel(offsetMinutes) {
  // Input: offsetMinutes (number)
  // Output: string
  // Description: Formats minute offset as UTC+HH:MM or UTC-HH:MM label.
  // Step 1: Determine positive/negative sign from offset value.
  // Step 2: Convert absolute minutes into hours and remainder minutes.
  // Step 3: Left-pad values and assemble UTC label string.
  // Example: -240 becomes "UTC-04:00".
  const sign = offsetMinutes >= 0 ? '+' : '-';
  const absoluteMinutes = Math.abs(offsetMinutes);
  const hours = String(Math.floor(absoluteMinutes / 60)).padStart(2, '0');
  const minutes = String(absoluteMinutes % 60).padStart(2, '0');
  return `UTC${sign}${hours}:${minutes}`;
}

// Build a list of time zone options with offsets for UI dropdowns
export function buildTimeZoneOptions() {
  // Input: none
  // Output: Array<{value,label,group,offset,offsetMinutes}>
  // Description: Builds unique and sorted timezone dropdown options used in periodic sync UI.
  // Step 1: Read supported timezone names and normalize aliases.
  // Step 2: Compute each timezone offset and build display labels.
  // Step 3: Remove duplicates by timezone key.
  // Step 4: Sort by offset first, then alphabetically for stable display.
  // Example: item label "UTC+05:30 — Asia/Kolkata".
  // Get supported time zones
  const zones = supportedTimeZones();
  // Map each time zone to an object with value, label, group, and offset info
  // for eg: { value: "America/New_York", label: "UTC-05:00 — America/New_York", group: "America", offset: "UTC-05:00", offsetMinutes: -300 }
  const items = zones.map(z => {
    const tz = normalizeTimeZone(z);

    const group = tz.includes('/') ? tz.split('/')[0] : 'Other';
    let offsetMinutes = 0;
    let offset = 'UTC+00:00';

    // Calculate the offset in minutes and format it, but if it fails (e.g. invalid tz), fallback to just getting the label
    try {
      offsetMinutes = getOffsetMinutes(tz);
      offset = formatOffsetLabel(offsetMinutes);
    } catch (_) {
      offsetMinutes = 0;
      offset = 'UTC+00:00';
    }

    return {
      value: tz,
      label: `${offset} — ${tz}`,
      group,
      offset,
      offsetMinutes
    };
  });

  // Remove duplicates by using a Map keyed by the time zone value (e.g. "America/New_York")
  const uniqueMap = new Map();
  items.forEach(item => uniqueMap.set(item.value, item));

  const uniqueItems = Array.from(uniqueMap.values());

  // Sort: First by offsetMinutes (e.g. -300 for UTC-05:00), then alphabetically by value to ensure consistent order for time zones with the same offset
  uniqueItems.sort(
    (a, b) => a.offsetMinutes - b.offsetMinutes || a.value.localeCompare(b.value)
  );

  // Eg: [ { value: "America/New_York", label: "UTC-05:00 — America/New_York", group: "America", offset: "UTC-05:00", offsetMinutes: -300 }, ... ]
  return uniqueItems;
}