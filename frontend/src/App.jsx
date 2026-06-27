import { useState } from "react"
import MapView from "./components/MapView"
import SearchPanel from "./components/SearchPanel"

function App() {
  const [route, setRoute] = useState(null)
  console.log("route:", route) 
  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <SearchPanel onRouteFound={setRoute} />
      <MapView route={route} />
    </div>
  )
}
 // add this line temporarily
export default App