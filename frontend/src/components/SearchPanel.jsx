import { useState } from "react"
import axios from "axios"

const API = "http://127.0.0.1:8000"

function SearchPanel({ onRouteFound }) {
  const [origin, setOrigin]           = useState("")
  const [destination, setDestination] = useState("")
  const [mode, setMode]               = useState("fastest")
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState(null)

  async function handleSearch() {
    setLoading(true)
    setError(null)

    try {
      // step 1 — fuzzy search for origin stop
      const originRes = await axios.get(`${API}/stops`, {
        params: { q: origin }
      })
      const originId = originRes.data[0].id  // take top match

      // step 2 — fuzzy search for destination stop
      const destRes = await axios.get(`${API}/stops`, {
        params: { q: destination }
      })
      const destId = destRes.data[0].id

      // step 3 — get route
      const routeRes = await axios.post(`${API}/route`, {
        origin: originId,
        destination: destId,
        mode: mode
      })

      onRouteFound(routeRes.data)  // send result up to App.jsx

    } catch (err) {
      setError("Could not find route. Try different stop names.")
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
      zIndex: 1000
    }}>
      <h2 style={{ fontSize: "18px", fontWeight: "600" }}>
        Delhi Transit Planner
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <label style={{ fontSize: "13px", color: "#666" }}>From</label>
        <input
          type="text"
          placeholder="e.g. Rajiv Chowk"
          value={origin}
          onChange={e => setOrigin(e.target.value)}
          style={inputStyle}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <label style={{ fontSize: "13px", color: "#666" }}>To</label>
        <input
          type="text"
          placeholder="e.g. Dilshad Garden"
          value={destination}
          onChange={e => setDestination(e.target.value)}
          style={inputStyle}
        />
      </div>

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
        disabled={loading || !origin || !destination}
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

      {error && (
        <p style={{ color: "red", fontSize: "13px" }}>{error}</p>
      )}
    </div>
  )
}

const inputStyle = {
  padding: "0.6rem 0.75rem",
  border: "1px solid #ddd",
  borderRadius: "8px",
  fontSize: "14px",
  outline: "none",
  width: "100%"
}

export default SearchPanel