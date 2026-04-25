// Smart City IoT — Mock Data Layer
// 120 sensors · 6 districts · realistic operational data
// No backend required — all data generated deterministically

// ---- Time helpers ----
function _ago(minutes) {
  return new Date(Date.now() - minutes * 60 * 1000).toISOString();
}
function _timeAgo(iso) {
  if (!iso) return 'Never';
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ---- Deterministic PRNG (seed → 0..1) ----
function _r(seed) {
  let h = (seed * 2654435761) & 0xFFFFFFFF;
  h ^= h >>> 16;
  h = (h * 2246822519) & 0xFFFFFFFF;
  h ^= h >>> 13;
  return (h & 0x7FFFFFFF) / 0x7FFFFFFF;
}

// ---- Battery helpers ----
// LoRaWAN primary lithium (ER-type): 2.0 V depleted → 3.6 V full
function _voltToPercent(v) {
  return Math.min(100, Math.max(0, Math.round(((v - 2.0) / 1.6) * 100)));
}
function _battHealth(pct) {
  if (pct > 30) return 'healthy';
  if (pct > 15) return 'warning';
  return 'critical';
}
function _battLifetime(pct, capacityMah, dailyMah) {
  const days = (pct / 100) * capacityMah / dailyMah;
  if (days > 730) return `~${(days / 365).toFixed(1)} years remaining`;
  if (days > 60)  return `~${Math.round(days / 30)} months remaining`;
  if (days > 7)   return `~${Math.round(days)} days remaining`;
  return 'Replace immediately';
}
function _battInsight(pct) {
  if (pct > 30) return 'Battery stable – no immediate action required';
  if (pct > 15) return 'Low battery – schedule replacement within 3 months';
  return 'Critical battery – immediate replacement required';
}

// ---- Sensor type config ----
const TYPE_META = {
  parking:       { label: 'Parking Sensor',      prefix: 'P',  capacityMah: 3600,  dailyMah: 0.4 },
  weather:       { label: 'Weather Station',      prefix: 'W',  capacityMah: 8500,  dailyMah: 0.9 },
  environmental: { label: 'Environmental Sensor', prefix: 'E',  capacityMah: 3600,  dailyMah: 0.5 },
  air_quality:   { label: 'Air Quality Monitor',  prefix: 'AQ', capacityMah: 19000, dailyMah: 2.1 },
};

// ---- District layout: [parking, weather, env, air_quality] ----
const DISTRICTS = [
  { name: 'Marktplatz',           lat: 48.8371, lng: 10.0934, dist: [8, 3, 5, 4] },
  { name: 'Bahnhof',              lat: 48.8355, lng: 10.0977, dist: [6, 4, 5, 5] },
  { name: 'Stadtpark',            lat: 48.8390, lng: 10.0890, dist: [2, 5, 8, 3] },
  { name: 'Schulzentrum',         lat: 48.8422, lng: 10.0858, dist: [5, 3, 6, 4] },
  { name: 'Industriegebiet Nord', lat: 48.8450, lng: 10.0790, dist: [8, 4, 4, 7] },
  { name: 'Ostalbkreis Ost',      lat: 48.8340, lng: 10.1050, dist: [9, 3, 6, 5] },
];
// totals: 38 parking + 22 weather + 34 env + 28 air = 122 → close to 120 ✓

// ---- Generate sensors ----
const SENSORS = [];
{
  const TYPES = ['parking', 'weather', 'environmental', 'air_quality'];
  let id = 1;
  DISTRICTS.forEach((d, di) => {
    TYPES.forEach((type, ti) => {
      const count = d.dist[ti];
      const meta  = TYPE_META[type];
      for (let i = 0; i < count; i++) {
        const seed = di * 1000 + ti * 100 + i;

        // Battery: voltage between 2.1 V and 3.55 V
        const battV   = 2.1 + _r(seed * 3 + 1) * 1.45;
        const battPct = _voltToPercent(battV);

        // Status: ~82% online, ~10% unstable, ~8% offline
        const sr = _r(seed * 7 + 3);
        const status = sr < 0.08 ? 'offline' : sr < 0.18 ? 'unstable' : 'online';

        // Last-seen: offline = 1–6 h ago, unstable = 20–60 min, online = 1–14 min
        const lastMin = status === 'offline'   ? Math.round(60  + _r(seed * 11) * 300)
                      : status === 'unstable'  ? Math.round(20  + _r(seed * 11) * 40)
                      :                          Math.round(1   + _r(seed * 11) * 13);

        // Current reading (deterministic but plausible)
        let readings = [];
        if (type === 'parking') {
          readings = [{ param: 'Parking', value: _r(seed*5) > 0.45 ? 'Occupied' : 'Available', unit: '' }];
        } else if (type === 'weather') {
          readings = [
            { param: 'Temperature', value: +(18 + _r(seed*5)*10).toFixed(1), unit: '°C' },
            { param: 'Humidity',    value: +(45 + _r(seed*6)*40).toFixed(1), unit: '%'  },
            { param: 'Rainfall',    value: +(_r(seed*7)*3).toFixed(2),        unit: 'mm' },
          ];
        } else if (type === 'environmental') {
          readings = [
            { param: 'Temperature', value: +(16 + _r(seed*5)*12).toFixed(1), unit: '°C' },
            { param: 'Humidity',    value: +(40 + _r(seed*6)*45).toFixed(1), unit: '%'  },
          ];
        } else { // air_quality
          readings = [
            { param: 'CO₂',   value: Math.round(400 + _r(seed*5)*900), unit: 'ppm'    },
            { param: 'PM2.5', value: +(2 + _r(seed*6)*28).toFixed(1),  unit: 'µg/m³' },
            { param: 'NO₂',   value: +(5 + _r(seed*7)*45).toFixed(1),  unit: 'µg/m³' },
          ];
        }

        SENSORS.push({
          id,
          unique_id: `${meta.prefix}-${String(di+1).padStart(2,'0')}-${String(id).padStart(3,'0')}`,
          name: `${meta.label} ${meta.prefix}${di+1}-${String(i+1).padStart(2,'0')}`,
          type,
          location: d.name,
          lat: d.lat + (_r(seed*13) - 0.5) * 0.005,
          lng: d.lng + (_r(seed*17) - 0.5) * 0.008,
          status,
          battery_pct:     battPct,
          battery_voltage: +battV.toFixed(2),
          battery_capacity_mah: meta.capacityMah,
          battery_daily_mah:    meta.dailyMah,
          lastMin,
          readings,
        });
        id++;
      }
    });
  });
}

// ---- Alerts ----
// Realistic: connectivity, gateway, hardware, firmware, battery
const ALERTS = [
  // CRITICAL — gateway failure, multi-sensor
  {
    id: 1, sensor_ids: [3,4,5,6,7,8,9,10], location: 'Stadtpark',
    severity: 'critical', root_cause: 'gateway',
    confidence: 94,
    alert_type: 'Gateway Failure',
    message: '8 Sensoren offline – Gateway-Ausfall Stadtpark',
    explanation: 'Alle betroffenen Sensoren nutzen denselben LoRaWAN-Gateway. Letzter Kontakt vor 2h 14min. Kein Heartbeat empfangen.',
    status: 'in_progress', assigned_to: 'Techniker A. Müller',
    recommended_action: 'Gateway vor Ort prüfen, Stromversorgung und Backhaul-Verbindung kontrollieren',
    created_at: _ago(134), resolved_at: null,
  },
  // CRITICAL — battery critical
  {
    id: 2, sensor_ids: [18], location: 'Bahnhof',
    severity: 'critical', root_cause: 'battery',
    confidence: 99,
    alert_type: 'Battery Critical',
    message: 'Sensor AQ-02-018: Batterie bei 9% (3.04 V)',
    explanation: 'Batteriespannung unterschreitet den kritischen Schwellwert von 3.1 V. Geschätzte Restlaufzeit unter 2 Wochen.',
    status: 'open', assigned_to: null,
    recommended_action: 'Batteriewechsel beauftragen – ER26500 Lithium-Primärzelle',
    created_at: _ago(48), resolved_at: null,
  },
  // MEDIUM — hardware failure (single sensor)
  {
    id: 3, sensor_ids: [55], location: 'Industriegebiet Nord',
    severity: 'medium', root_cause: 'hardware',
    confidence: 81,
    alert_type: 'Hardware Issue',
    message: 'Sensor E-05-055: Antwortet nicht trotz gutem Signal (RSSI –72 dBm)',
    explanation: 'Uplinks werden empfangen, Downlinks werden jedoch nicht beantwortet. Starkes Signal schließt Konnektivität aus. Möglicher MCU-Hänger oder Sensorausfall.',
    status: 'open', assigned_to: null,
    recommended_action: 'Remote-Reset versuchen, bei Fehlschlag Hardware-Austausch einplanen',
    created_at: _ago(210), resolved_at: null,
  },
  // MEDIUM — unstable connectivity
  {
    id: 4, sensor_ids: [72, 73, 74], location: 'Ostalbkreis Ost',
    severity: 'medium', root_cause: 'connectivity',
    confidence: 76,
    alert_type: 'Connectivity Unstable',
    message: '3 Sensoren: unregelmäßige Übertragung (Ostalbkreis Ost)',
    explanation: 'Sensoren haben die letzten 2–4 Übertragungen ausgelassen. Signal schwach (RSSI –104 bis –108 dBm). Mögliche Abschirmung oder Interferenz.',
    status: 'in_progress', assigned_to: 'Techniker B. Koch',
    recommended_action: 'Signalstärke vor Ort messen, ggf. Antennenausrichtung korrigieren',
    created_at: _ago(320), resolved_at: null,
  },
  // MEDIUM — firmware anomaly
  {
    id: 5, sensor_ids: [101], location: 'Marktplatz',
    severity: 'medium', root_cause: 'software',
    confidence: 68,
    alert_type: 'Firmware Anomaly',
    message: 'Sensor W-01-101: Unplausible Werte seit Firmware-Update v2.4.1',
    explanation: 'Temperatursensor meldet –127.5 °C – typischer Initialisierungsfehler nach Firmware-Rollout. Letzte plausible Messung vor 6h.',
    status: 'open', assigned_to: null,
    recommended_action: 'Firmware-Rollback auf v2.4.0 oder Neustart mit Factory-Reset',
    created_at: _ago(380), resolved_at: null,
  },
  // LOW — battery warning (not urgent)
  {
    id: 6, sensor_ids: [29, 31, 44, 88], location: 'Marktplatz / Schulzentrum',
    severity: 'low', root_cause: 'battery',
    confidence: 97,
    alert_type: 'Battery Warning',
    message: '4 Sensoren: Batterie 16–28% – Wartung in 3–6 Monaten',
    explanation: 'Batteriespannungen zwischen 3.12 V und 3.26 V. Sensoren sind weiterhin voll funktionsfähig. Präventiver Hinweis für Wartungsplanung.',
    status: 'open', assigned_to: null,
    recommended_action: 'Batteriewechsel im nächsten regulären Wartungszyklus einplanen',
    created_at: _ago(720), resolved_at: null,
  },
  // LOW — temporary delay (not critical)
  {
    id: 7, sensor_ids: [38], location: 'Bahnhof',
    severity: 'low', root_cause: 'connectivity',
    confidence: 55,
    alert_type: 'Temporary Delay',
    message: 'Sensor P-02-038: 2 Übertragungen ausgelassen – Unstable',
    explanation: 'Sensor hat 2 aufeinanderfolgende Übertragungen verpasst. Signal normal. Möglicherweise temporäre Interferenz. Wird nicht als Offline gewertet.',
    status: 'open', assigned_to: null,
    recommended_action: 'Beobachten – bei weiteren Ausfällen eskalieren',
    created_at: _ago(25), resolved_at: null,
  },
  // Resolved examples
  {
    id: 8, sensor_ids: [12], location: 'Marktplatz',
    severity: 'medium', root_cause: 'hardware',
    confidence: 89,
    alert_type: 'Hardware Issue',
    message: 'Sensor P-01-012: Fehlerhaftes Parksensor-Modul ersetzt',
    explanation: 'Magnetometer meldete konstant "Besetzt" trotz leerem Stellplatz. Modul getauscht.',
    status: 'resolved', assigned_to: 'Techniker A. Müller',
    recommended_action: 'Erledigt – Sensor kalibriert und in Betrieb',
    created_at: _ago(2880), resolved_at: _ago(2400),
  },
  {
    id: 9, sensor_ids: [67, 68], location: 'Schulzentrum',
    severity: 'low', root_cause: 'software',
    confidence: 72,
    alert_type: 'Config Mismatch',
    message: 'Sensoren E-04-067/068: Falsche Payload-Dekodierung nach Update',
    explanation: 'Codec-Version stimmte nicht mit Firmware überein. Remote-Fix eingespielt.',
    status: 'resolved', assigned_to: 'Techniker B. Koch',
    recommended_action: 'Erledigt – Codec aktualisiert',
    created_at: _ago(4320), resolved_at: _ago(3960),
  },
];

// ---- Data quality issues ----
const DATA_QUALITY = [
  { issue: 'Fehlende Geokoordinaten',    count: 5,  severity: 'low',    detail: 'Sensoren ohne lat/lng – nicht auf Karte darstellbar' },
  { issue: 'Fehlende Batterieinformation',count: 9, severity: 'low',    detail: 'Kein Voltage-Wert übermittelt – Ladestand unbekannt' },
  { issue: 'Inkonsistente Messwerte',     count: 3,  severity: 'medium', detail: 'Temperaturen außerhalb plausiblem Bereich (< –40°C oder > 85°C)' },
  { issue: 'Fehlende Metadaten',          count: 7,  severity: 'low',    detail: 'Sensoren ohne Standort-Zuweisung oder Gerätebeschreibung' },
];

// ---- Trend generator (deterministic last-24h curve) ----
function _trend(param) {
  const now  = new Date();
  const labels = [], values = [];
  let unit = '';
  for (let h = 23; h >= 0; h--) {
    const hour = new Date(now - h * 3600000).getHours();
    labels.push(`${String(hour).padStart(2,'0')}:00`);
    let v;
    if (param === 'temperature') {
      v = +(18 + 6 * Math.sin((hour - 6) * Math.PI / 12) + (_r(hour * 31 + 7) - 0.5) * 1.5).toFixed(1);
      unit = '°C';
    } else if (param === 'humidity') {
      v = +(58 - 14 * Math.sin((hour - 6) * Math.PI / 12) + (_r(hour * 37 + 11) - 0.5) * 3).toFixed(1);
      unit = '%';
    } else if (param === 'co2') {
      const peak = (hour >= 7 && hour <= 9) || (hour >= 16 && hour <= 19) ? 1 : 0;
      v = Math.round(420 + peak * 350 + _r(hour * 41 + 13) * 80);
      unit = 'ppm';
    } else if (param === 'pm25') {
      v = +(4 + _r(hour * 43 + 17) * 18).toFixed(1);
      unit = 'µg/m³';
    }
    values.push(v);
  }
  return { labels, values, unit };
}

// ---- Sensor name lookup ----
const SENSOR_MAP = Object.fromEntries(SENSORS.map(s => [s.id, s.name]));

// ============================================================
// Public API — same interface used by all HTML pages
// ============================================================

async function dbGetStats() {
  const total     = SENSORS.length;
  const online    = SENSORS.filter(s => s.status === 'online').length;
  const unstable  = SENSORS.filter(s => s.status === 'unstable').length;
  const offline   = SENSORS.filter(s => s.status === 'offline').length;
  const alerts    = ALERTS.filter(a => a.status !== 'resolved').length;
  const districts = [...new Set(SENSORS.map(s => s.location))].length;
  return { total_sensors: total, online_sensors: online, unstable_sensors: unstable,
           offline_sensors: offline, active_alerts: alerts, districts_count: districts,
           online_pct: Math.round(online / total * 1000) / 10 };
}

async function dbGetSensors() {
  return SENSORS.map(s => {
    const meta = TYPE_META[s.type];
    return {
      id: s.id, name: s.name, unique_id: s.unique_id, type: s.type,
      location: s.location, status: s.status,
      battery_pct:     s.battery_pct,
      battery_voltage: s.battery_voltage,
      battery_health:  _battHealth(s.battery_pct),
      battery_capacity_mah: s.battery_capacity_mah,
      battery_lifetime: _battLifetime(s.battery_pct, s.battery_capacity_mah, s.battery_daily_mah),
      battery_insight:  _battInsight(s.battery_pct),
      last_seen:     _ago(s.lastMin),
      last_seen_ago: _timeAgo(_ago(s.lastMin)),
      lat: s.lat, lng: s.lng,
      readings: s.readings,
    };
  });
}

async function dbGetMapSensors() {
  return SENSORS.map(s => ({
    id: s.id, name: s.name, lat: s.lat, lng: s.lng,
    type: s.type, status: s.status, battery: s.battery_pct,
  }));
}

async function dbGetAlerts(tab = 'all') {
  const ROOT_ICON = { battery: '🔋', connectivity: '📡', gateway: '🌐', hardware: '⚙️', software: '🧠' };
  const all = ALERTS.map(a => ({
    ...a,
    sensor_name: a.sensor_ids.length === 1
      ? (SENSOR_MAP[a.sensor_ids[0]] || `Sensor #${a.sensor_ids[0]}`)
      : `${a.sensor_ids.length} Sensoren (${a.location})`,
    root_cause_icon: ROOT_ICON[a.root_cause] || '❓',
    created_ago: _timeAgo(a.created_at),
    severity_display: { critical: 'Critical', medium: 'Warning', low: 'Info' }[a.severity] || a.severity,
    affected_count: a.sensor_ids.length,
  }));
  const unresolved  = all.filter(a => a.status !== 'resolved').length;
  const critical    = all.filter(a => a.severity === 'critical' && a.status !== 'resolved').length;
  const resolved24  = all.filter(a => a.status === 'resolved').length;
  let filtered = all;
  if (tab === 'unresolved') filtered = all.filter(a => a.status !== 'resolved');
  else if (tab === 'resolved') filtered = all.filter(a => a.status === 'resolved');
  return { total: all.length, unresolved, critical, resolved_24h: resolved24, alerts: filtered };
}

async function dbGetTrends(parameter = 'temperature') {
  return { parameter, ..._trend(parameter) };
}

async function dbGetLocations() {
  const locMap = {};
  SENSORS.forEach(s => {
    if (!locMap[s.location]) locMap[s.location] = { total: 0, online: 0, unstable: 0 };
    locMap[s.location].total++;
    if (s.status === 'online')   locMap[s.location].online++;
    if (s.status === 'unstable') locMap[s.location].unstable++;
  });
  const locations = Object.entries(locMap).sort(([a],[b]) => a.localeCompare(b)).map(([name, d]) => ({
    name, total: d.total, online: d.online, unstable: d.unstable,
    uptime: d.total > 0 ? Math.round(d.online / d.total * 100) : 0,
  }));
  const map_sensors = SENSORS.map(s => ({
    id: s.id, name: s.name, lat: s.lat, lng: s.lng, type: s.type, status: s.status,
  }));
  return { locations, map_sensors };
}

async function dbGetDataQuality() {
  return DATA_QUALITY;
}
