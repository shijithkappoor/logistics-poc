import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
function App() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return; const map = new maplibregl.Map({ container: ref.current, style: 'https://demotiles.maplibre.org/style.json', center: [-79.3832, 43.6532], zoom: 9 });
    fetch('http://localhost:8001/warehouses').then(r => r.json()).then(ws => ws.forEach((w: any) => new maplibregl.Marker({ color: '#0b5' }).setLngLat([w.lon, w.lat]).setPopup(new maplibregl.Popup().setText(w.name)).addTo(map)));
    return () => map.remove();
  }, [])
  return <div ref={ref} style={{ height: '100vh' }} />
}
export default App
