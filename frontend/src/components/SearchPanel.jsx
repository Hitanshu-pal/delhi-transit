import { useState } from "react"
import axios from "axios"
import ResultsPanel from "./ResultsPanel"

const API = "http://127.0.0.1:8000"

function StopInput({ label, value, onSelect, mode, onUseLocation, showLocationButton }) {
  const [query, setQuery] = useState(value || "")
  const [suggestions, setSuggestions] = useState([])
  const [locating, setLocating] = useState(false)

  async function handleChange(e) {
    const val = e.target.value
    setQuery(val)
    if (val.length < 2) { setSuggestions([]); return }

    const params = { q: val }
    if (mode === "metro_only") params.mode = "metro"
    if (mode === "bus_only")   params.mode = "bus"

    const res = await axios.get(`${API}/stops`, { params })
    setSuggestions(res.data)
  }

  function handleSelect(stop) {
    setQuery(stop.name)
    setSuggestions([])
    onSelect(stop)
  }

  async function handleUseLocation() {
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords
        try {
          const res = await axios.get(`${API}/geocode`, {
            params: { lat: latitude, lon: longitude }
          })
          if (res.data.error) {
            alert("Could not find a nearby stop.")
            setLocating(false)
            return
          }
          setQuery(`Current location (near ${res.data.stop_name})`)
          onSelect({
            id: res.data.nearest_stop,
            name: res.data.stop_name,
            mode: res.data.stop_mode,
            lat: res.data.lat,
            lon: res.data.lon
          })
        } catch {
          alert("Could not fetch your location-based route.")
        }
        setLocating(false)
      },
      () => {
        alert("Location access denied. Please allow location access or type a stop name.")
        setLocating(false)
      }
    )
  }

  return (
    <div style={{ position: "relative" }}>
      <label style={{ fontSize: "13px", color: "#666" }}>{label}</label>
      <div style={{ display: "flex", gap: "6px" }}>
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder="Type a stop name..."
          style={inputStyle}
        />
        {showLocationButton && (
          <button
            type="button"
            onClick={handleUseLocation}
            disabled={locating}
            title="Use current location"
            style={locationButtonStyle}
          >
            {locating ? "..." : "📍"}
          </button>
        )}
      </div>
      {suggestions.length > 0 && (
        <div style={{
          position: "absolute",
          top: "100%",
          left: 0,
          right: 0,
          background: "#fff",
          border: "1px solid #ddd",
          borderRadius: "8px",
          zIndex: 9999,
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          maxHeight: "220px",
          overflowY: "auto"
        }}>
          {suggestions.map(stop => (
            <div
              key={stop.id}
              onClick={() => handleSelect(stop)}
              style={{
                padding: "0.6rem 0.75rem",
                cursor: "pointer",
                fontSize: "13px",
                borderBottom: "1px solid #f0f0f0",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
              onMouseEnter={e => e.currentTarget.style.background = "#f5f5f5"}
              onMouseLeave={e => e.currentTarget.style.background = "#fff"}
            >
              <span>{stop.name}</span>
              <span style={{
                fontSize: "11px",
                color: stop.mode === "metro" ? "#1a73e8" : "#34a853",
                fontWeight: "500"
              }}>
                {stop.mode.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SearchPanel({ onRouteFound }) {
  const [originId, setOriginId] = useState(null)
  const [destId, setDestId]     = useState(null)
  const [mode, setMode]         = useState("fastest")
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [route, setRoute]       = useState(null)

  async function handleSearch() {
    if (!originId || !destId) {
      setError("Please select stops from the dropdown")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API}/route`, {
        origin: originId,
        destination: destId,
        mode: mode
      })
      onRouteFound(res.data)
      setRoute(res.data)
    } catch {
      setError("Could not find route.")
    }
    setLoading(false)
  }

  return (
    <div style={{
      width: "350px",
      padding: "1.5rem",
      background: "#ffffff",
      boxShadow: "2px 0 8px rgba(0,0,0,0.1)",
      display: "flex",
      flexDirection: "column",
      gap: "1rem",
      zIndex: 1000,
      overflowY: "auto"
    }}>
      <h2 style={{ fontSize: "18px", fontWeight: "600" }}>
        Delhi Transit Planner
      </h2>

      <StopInput
        label="From"
        onSelect={s => setOriginId(s.id)}
        mode={mode}
        showLocationButton={true}
      />
      <StopInput
        label="To"
        onSelect={s => setDestId(s.id)}
        mode={mode}
        showLocationButton={false}
      />

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <label style={{ fontSize: "13px", color: "#666" }}>Mode</label>
        <select
          value={mode}
          onChange={e => setMode(e.target.value)}
          style={inputStyle}
        >
          <option value="fastest">Fastest route</option>
          <option value="fewest_transfers">Fewest transfers</option>
          <option value="metro_only">Metro only</option>
          <option value="bus_only">Bus only</option>
        </select>
      </div>

      <button
        onClick={handleSearch}
        disabled={loading || !originId || !destId}
        style={{
          padding: "0.75rem",
          background: loading ? "#ccc" : "#1a73e8",
          color: "white",
          border: "none",
          borderRadius: "8px",
          fontSize: "14px",
          fontWeight: "500",
          cursor: loading ? "not-allowed" : "pointer"
        }}
      >
        {loading ? "Finding route..." : "Find Route"}
      </button>

      {error && <p style={{ color: "red", fontSize: "13px" }}>{error}</p>}

      <ResultsPanel route={route} />
    </div>
  )
}

const inputStyle = {
  padding: "0.6rem 0.75rem",
  border: "1px solid #ddd",
  borderRadius: "8px",
  fontSize: "14px",
  width: "100%"
}

const locationButtonStyle = {
  padding: "0.6rem 0.7rem",
  border: "1px solid #ddd",
  borderRadius: "8px",
  background: "#fff",
  cursor: "pointer",
  fontSize: "14px",
  flexShrink: 0
}

export default SearchPanel
