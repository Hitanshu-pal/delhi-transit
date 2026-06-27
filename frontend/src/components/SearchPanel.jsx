import { useState, useRef } from "react"
import axios from "axios"
import ResultsPanel from "./ResultsPanel"

const API = "http://127.0.0.1:8000"

function StopInput({ label, onSelect,mode }) {
  const [query, setQuery]           = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [selected, setSelected]     = useState(null)

  async function handleChange(e) {
    const val = e.target.value
    setQuery(val)
    setSelected(null)
    if (val.length < 2) { setSuggestions([]); return }
    
    // pass mode to filter results
    const params = { q: val }
    if (mode === "metro_only") params.mode = "metro"
    if (mode === "bus_only")   params.mode = "bus"
    
    const res = await axios.get(`${API}/stops`, { params })
    setSuggestions(res.data)
  }

  function handleSelect(stop) {
    setQuery(stop.name)
    setSelected(stop)
    setSuggestions([])
    onSelect(stop)
  }

  return (
    <div style={{ position: "relative" }}>
      <label style={{ fontSize: "13px", color: "#666" }}>{label}</label>
      <input
        type="text"
        value={query}
        onChange={handleChange}
        placeholder="Type a stop name..."
        style={inputStyle}
      />
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
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
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
              onMouseEnter={e => e.target.style.background = "#f5f5f5"}
              onMouseLeave={e => e.target.style.background = "#fff"}
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
  const [originId, setOriginId]   = useState(null)
  const [destId, setDestId]       = useState(null)
  const [mode, setMode]           = useState("fastest")
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [route, setRoute]         = useState(null)

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

      <StopInput label="From" onSelect={s => setOriginId(s.id)} mode={mode} />
      <StopInput label="To"   onSelect={s => setDestId(s.id)} mode={mode} />

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

export default SearchPanel