import { useEffect, useState } from "react";
import type { Sensor, SensorUrgency } from "@/lib/sensors";

const urgencyColor: Record<SensorUrgency, string> = {
  critical: "#ef4444",
  medium: "#f59e0b",
  low: "#3b82f6",
};

export default function SensorsMap({
  sensors,
  onSelect,
}: {
  sensors: Sensor[];
  onSelect?: (s: Sensor) => void;
}) {
  const [mounted, setMounted] = useState(false);
  const [mods, setMods] = useState<{
    MapContainer: any;
    TileLayer: any;
    CircleMarker: any;
    Popup: any;
  } | null>(null);

  useEffect(() => {
    setMounted(true);
    Promise.all([
      import("react-leaflet"),
      import("leaflet/dist/leaflet.css"),
    ]).then(([rl]) => {
      setMods({
        MapContainer: rl.MapContainer,
        TileLayer: rl.TileLayer,
        CircleMarker: rl.CircleMarker,
        Popup: rl.Popup,
      });
    });
  }, []);

  if (!mounted || !mods) {
    return (
      <div className="h-56 w-full animate-pulse rounded-2xl border border-border bg-muted" />
    );
  }

  const { MapContainer, TileLayer, CircleMarker, Popup } = mods;

  return (
    <div className="overflow-hidden rounded-2xl border border-border shadow-sm">
      <MapContainer
        center={[48.8378, 10.0939]}
        zoom={13}
        scrollWheelZoom={false}
        style={{ height: "224px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {sensors.map((s) => (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lng]}
            radius={9}
            pathOptions={{
              color: "#ffffff",
              weight: 2,
              fillColor: urgencyColor[s.urgency],
              fillOpacity: 0.95,
            }}
            eventHandlers={{
              click: () => onSelect?.(s),
            }}
          >
            <Popup>
              <div style={{ fontFamily: "inherit", minWidth: 140 }}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{s.name}</div>
                <div style={{ fontSize: 11, color: "#666" }}>
                  {s.code} · {s.urgency}
                </div>
                <div style={{ fontSize: 11, marginTop: 4 }}>{s.location}</div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
