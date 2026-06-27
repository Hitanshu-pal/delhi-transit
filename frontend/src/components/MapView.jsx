import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from "react-leaflet"

const MODE_COLORS = {
  metro: "#1a73e8",
  bus:   "#34a853",
  walk:  "#888888",
}
const ROUTE_COLORS = {
  // Red Line
  "0": "#e53935", "1": "#e53935", "18": "#e53935", "19": "#e53935",
  // Yellow Line
  "2": "#FDD835", "3": "#FDD835", "4": "#FDD835", "20": "#FDD835",
  "21": "#FDD835", "22": "#FDD835",
  // Blue Line
  "5": "#1565C0", "6": "#1565C0", "23": "#1565C0", "24": "#1565C0",
  // Green Line
  "7": "#43A047", "8": "#43A047", "25": "#43A047", "26": "#43A047",
  // Violet Line
  "9": "#6A1B9A", "10": "#6A1B9A", "27": "#6A1B9A", "28": "#6A1B9A",
  // Magenta Line
  "12": "#AD1457", "30": "#AD1457",
  // Pink Line
  "11": "#F06292", "29": "#F06292",
  // Gray Line
  "13": "#757575", "31": "#757575",
  // Orange/Airport Line
  "14": "#FF6F00", "32": "#FF6F00",
  // Aqua Line
  "16": "#00ACC1", "17": "#00ACC1", "34": "#00ACC1", "35": "#00ACC1",
  // Rapid Metro
  "15": "#00897B", "33": "#00897B",
  // Bus — neutral
  "bus": "#90A4AE",
  // Walk
  "walk": "#BDBDBD",
}
function buildSegments(path) {
  if (!path || path.length === 0) return []

  const segments = []
  let current = {
    mode: path[0].mode,
    route_id: path[0].route_id,
    points: [[path[0].lat, path[0].lon]]
  }

  for (let i = 1; i < path.length; i++) {
    const stop = path[i]
    // start new segment when mode OR route changes
    if (stop.mode === current.mode && stop.route_id === current.route_id) {
      current.points.push([stop.lat, stop.lon])
    } else {
      segments.push(current)
      current = {
        mode: stop.mode,
        route_id: stop.route_id,
        points: [[path[i-1].lat, path[i-1].lon], [stop.lat, stop.lon]]
      }
    }
  }
  segments.push(current)
  return segments
}

function MapView({ route }) {
  const segments = buildSegments(route?.path)

  return (
    <MapContainer
      center={[28.6139, 77.2090]}
      zoom={11}
      style={{ flex: 1, height: "100vh" }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {segments.map((seg, i) => {
  const color = seg.mode === "bus"  ? ROUTE_COLORS["bus"]
              : seg.mode === "walk" ? ROUTE_COLORS["walk"]
              : ROUTE_COLORS[seg.route_id] || "#333"
  return (
    <Polyline
      key={i}
      positions={seg.points}
      color={color}
      weight={5}
      opacity={0.85}
    />
  )
})}

      {route && route.path.map((stop, i) => (
        <CircleMarker
          key={i}
          center={[stop.lat, stop.lon]}
          radius={5}
          color={MODE_COLORS[stop.mode] || "#333"}
          fillColor={MODE_COLORS[stop.mode] || "#333"}
          fillOpacity={0.9}
        >
          <Popup>{stop.name}<br/><small>{stop.mode}</small></Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}

export default MapView