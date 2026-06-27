const MODE_ICONS = {
  metro: "🚇",
  bus:   "🚌",
  walk:  "🚶",
}

const MODE_LABELS = {
  metro: "Metro",
  bus:   "Bus",
  walk:  "Walk",
}
const ROUTE_NAMES = {
  "0": "Red Line", "1": "Red Line", "18": "Red Line", "19": "Red Line",
  "2": "Yellow Line", "3": "Yellow Line", "4": "Yellow Line",
  "20": "Yellow Line", "21": "Yellow Line", "22": "Yellow Line",
  "5": "Blue Line", "6": "Blue Line", "23": "Blue Line", "24": "Blue Line",
  "7": "Green Line", "8": "Green Line", "25": "Green Line", "26": "Green Line",
  "9": "Violet Line", "10": "Violet Line", "27": "Violet Line", "28": "Violet Line",
  "12": "Magenta Line", "30": "Magenta Line",
  "11": "Pink Line", "29": "Pink Line",
  "13": "Gray Line", "31": "Gray Line",
  "14": "Airport Line", "32": "Airport Line",
  "16": "Aqua Line", "17": "Aqua Line", "34": "Aqua Line", "35": "Aqua Line",
  "15": "Rapid Metro", "33": "Rapid Metro",
}
function groupLegs(path) {
  if (!path || path.length === 0) return []

  const legs = []
  let current = {
    mode: path[0].mode,
    route_id: path[0].route_id,
    stops: [path[0]]
  }

  for (let i = 1; i < path.length; i++) {
    const stop = path[i]
    if (stop.mode === current.mode && stop.route_id === current.route_id) {
      current.stops.push(stop)
    } else {
      legs.push(current)
      current = { mode: stop.mode, route_id: stop.route_id, stops: [stop] }
    }
  }
  legs.push(current)

  // remove single-stop legs with no route — these are just boarding points
  return legs.filter(leg => !(leg.stops.length === 1 && !leg.route_id))
}
function ResultsPanel({ route }) {
  if (!route) return null

  const legs = groupLegs(route.path)

  return (
    <div style={{
      marginTop: "1rem",
      borderTop: "1px solid #eee",
      paddingTop: "1rem"
    }}>
      <p style={{ fontSize: "13px", color: "#666", marginBottom: "0.75rem" }}>
        Total time: <strong>{route.cost} min</strong>
        {" · "}
        {legs.length - 1} transfer{legs.length !== 2 ? "s" : ""}
      </p>

      {legs.map((leg, i) => (
        <div key={i} style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: "0.75rem",
          alignItems: "flex-start"
        }}>
          <span style={{ fontSize: "20px" }}>{MODE_ICONS[leg.mode]}</span>
          <div>
            <p style={{ fontSize: "13px", fontWeight: "500", margin: 0 }}>
              {MODE_LABELS[leg.mode]}
              {leg.route_id && leg.mode === "metro" ? ` · ${ROUTE_NAMES[leg.route_id] || "Metro"}` : ""}            </p>
            <p style={{ fontSize: "12px", color: "#666", margin: "2px 0 0" }}>
              {leg.stops[0].name} → {leg.stops[leg.stops.length - 1].name}
              {leg.stops.length > 2 ? ` (${leg.stops.length - 1} stops)` : ""}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

export default ResultsPanel