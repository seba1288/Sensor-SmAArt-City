export type SensorUrgency = "critical" | "medium" | "low";
export type SensorCategory =
  | "Hardware"
  | "Battery"
  | "Software"
  | "Connectivity"
  | "Environment";
export type SensorStatus = "Open" | "Unstable";

export type Sensor = {
  id: string;
  name: string; // e.g. "Limesmuseum Weather"
  code: string; // e.g. "SN-014"
  district: string; // e.g. "Nord District"
  location: string; // e.g. "Aalen-Mitte · Stadtgarten"
  urgency: SensorUrgency;
  category: SensorCategory;
  status: SensorStatus;
  problem: string;
  why: string;
  recommendedAction: string;
  reportedAt: string;
  resolutionComment?: string;
  resolvedAt?: string;
  lat: number;
  lng: number;
};

export const initialSensors: Sensor[] = [
  {
    id: "a1",
    name: "Wasseralfingen Level",
    code: "SN-022",
    district: "Nord District",
    location: "Wasseralfingen · Pump Station 3",
    urgency: "critical",
    category: "Hardware",
    status: "Open",
    problem: "Sensor unresponsive despite strong signal — hardware issue.",
    why: "Signal strong (RSSI −85), neighbours online, no transmissions for 2+ hours.",
    recommendedAction: "Dispatch technician for on-site inspection and reboot.",
    reportedAt: "2 hr ago",
    lat: 48.8556,
    lng: 10.0967,
  },
  {
    id: "a2",
    name: "Reichsstädter Air",
    code: "SN-008",
    district: "Central District",
    location: "Reichsstädter Markt · Air Quality Mast",
    urgency: "critical",
    category: "Software",
    status: "Open",
    problem: "PM2.5 exceeded threshold (84 µg/m³).",
    why: "Sustained high reading consistent with traffic-related particulate event.",
    recommendedAction:
      "Verify reading vs neighbour stations, raise traffic-ops ticket.",
    reportedAt: "32 min ago",
    lat: 48.8378,
    lng: 10.0939,
  },
  {
    id: "a3",
    name: "Limesmuseum Weather",
    code: "SN-014",
    district: "West District",
    location: "Limesmuseum · Rooftop weather mast",
    urgency: "medium",
    category: "Battery",
    status: "Unstable",
    problem: "Battery below 15% — schedule replacement.",
    why: "Discharge rate 1.6%/day vs expected 0.8%/day — likely cold-weather effect.",
    recommendedAction: "Swap battery pack on next field visit.",
    reportedAt: "12 min ago",
    lat: 48.8401,
    lng: 10.0820,
  },
  {
    id: "a4",
    name: "Stadtgarten Parking",
    code: "SN-031",
    district: "Central District",
    location: "Stadtgarten · Parkdeck Süd, Bay 14",
    urgency: "medium",
    category: "Connectivity",
    status: "Open",
    problem: "No payload received this cycle — data quality issue.",
    why: "Last gateway uplink 47 min ago, neighbours nominal — likely antenna fault.",
    recommendedAction: "Re-seat antenna connector and verify enclosure seal.",
    reportedAt: "47 min ago",
    lat: 48.8392,
    lng: 10.0955,
  },
  {
    id: "a5",
    name: "Hochschule Soil Probe",
    code: "SN-004",
    district: "West District",
    location: "Hochschule Campus · Field plot B",
    urgency: "low",
    category: "Software",
    status: "Open",
    problem: "Firmware out of date — v2.1.0 → v2.2.0 available.",
    why: "Stability and power-management fixes shipped in v2.2.0.",
    recommendedAction: "Trigger OTA update during next maintenance window.",
    reportedAt: "3 hr ago",
    lat: 48.8294,
    lng: 10.0731,
  },
  {
    id: "a6",
    name: "Marktplatz Parking",
    code: "SN-019",
    district: "Central District",
    location: "Marktplatz · North entry, Bay 02",
    urgency: "low",
    category: "Software",
    status: "Open",
    problem: "Firmware update available — v2.4.0.",
    why: "v2.4.0 published — stability fixes for parking sensors.",
    recommendedAction: "Schedule OTA rollout for the parking fleet.",
    reportedAt: "1 hr ago",
    lat: 48.8385,
    lng: 10.0934,
  },
];
