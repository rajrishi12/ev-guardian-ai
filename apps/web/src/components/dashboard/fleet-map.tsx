"use client";

import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip } from "react-leaflet";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import "leaflet/dist/leaflet.css";

const RISK_COLOR = (p: number | null) => {
  const prob = p ?? 0;
  if (prob > 0.4) return "#ff5c5c";
  if (prob > 0.15) return "#f5a524";
  return "#00e5a0";
};

export function FleetMap() {
  const { data: depots, isLoading: depotsLoading } = useQuery({
    queryKey: ["depots"],
    queryFn: api.fleet.depots,
  });

  const { data: vehicles, isLoading: vehiclesLoading } = useQuery({
    queryKey: ["vehicles-map"],
    queryFn: () => api.fleet.vehicles({ limit: 100 }),
  });

  const isLoading = depotsLoading || vehiclesLoading;

  // India-wide default center
  const center: [number, number] = [22.5, 79.0];

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Live fleet map</CardTitle>
        <Badge variant="neutral">{depots?.length ?? 0} depots</Badge>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[420px] animate-pulse rounded-lg bg-surface-elevated" />
        ) : (
          <div className="h-[420px] overflow-hidden rounded-[var(--radius)] [&_.leaflet-container]:bg-[#0a0e16]">
            <MapContainer
              center={center}
              zoom={5}
              scrollWheelZoom
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors'
              />
              {vehicles?.map((v) => {
                const lat = v.current_lat ?? v.depot_lat;
                const lon = v.current_lon ?? v.depot_lon;
                return (
                  <CircleMarker
                    key={v.vehicle_id}
                    center={[lat, lon]}
                    radius={5}
                    pathOptions={{
                      color: RISK_COLOR(v.failure_probability),
                      fillColor: RISK_COLOR(v.failure_probability),
                      fillOpacity: 0.85,
                      weight: 1,
                    }}
                  >
                    <LeafletTooltip direction="top" offset={[0, -4]}>
                      <span style={{ fontFamily: "monospace", fontSize: 11 }}>
                        {v.vehicle_id} · {v.model}
                        <br />
                        SOH {v.final_soh_pct?.toFixed(1)}%
                      </span>
                    </LeafletTooltip>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
