import { useState, useEffect, useRef } from 'react'

// Define warehouse interface
interface Warehouse {
  id: string;
  name: string;
  lat: number;
  lon: number;
}

function App() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [warehouses, setWarehouses] = useState<Warehouse[]>([])
  const [mapLoaded, setMapLoaded] = useState(false)
  const [debugInfo, setDebugInfo] = useState('App component loaded')

  useEffect(() => {
    let maplibregl: any = null;

    const initializeMap = async () => {
      try {
        console.log('Starting map initialization...')
        setLoading(true)

        // Dynamically import MapLibre GL
        console.log('Importing MapLibre GL...')
        maplibregl = await import('maplibre-gl')

        // Import CSS
        await import('maplibre-gl/dist/maplibre-gl.css')
        console.log('MapLibre GL imported successfully')

        if (!mapContainer.current) {
          throw new Error('Map container not found')
        }

        // Fetch warehouses first
        console.log('Fetching warehouses...')
        const response = await fetch('http://localhost:8001/warehouses')
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }
        const warehouseData: Warehouse[] = await response.json()
        console.log('Warehouses loaded:', warehouseData)
        setWarehouses(warehouseData)

        // Wait a bit to ensure container is properly sized
        await new Promise(resolve => setTimeout(resolve, 100))

        // Force container to have dimensions
        if (mapContainer.current) {
          mapContainer.current.style.height = '100vh'
          mapContainer.current.style.width = '100vw'
        }

        // Create map
        console.log('Creating map...')
        map.current = new maplibregl.Map({
          container: mapContainer.current,
          style: 'https://demotiles.maplibre.org/style.json',
          center: [-79.3832, 43.6532],
          zoom: 9,
          attributionControl: false // Remove attribution for cleaner look
        })

        // Force resize after creation
        setTimeout(() => {
          if (map.current) {
            map.current.resize()
          }
        }, 200)

        // Handle map load
        map.current.on('load', () => {
          console.log('Map loaded successfully')
          setMapLoaded(true)
          setLoading(false)

          // Add warehouse markers
          warehouseData.forEach((warehouse) => {
            console.log(`Adding marker for: ${warehouse.name}`)
            new maplibregl.Marker({ color: '#0b5' })
              .setLngLat([warehouse.lon, warehouse.lat])
              .setPopup(new maplibregl.Popup().setText(warehouse.name))
              .addTo(map.current)
          })
        })

        // Handle map errors
        map.current.on('error', (e: any) => {
          console.error('Map error:', e)
          setError(`Map error: ${e.error?.message || 'Unknown error'}`)
          setLoading(false)
        })

      } catch (error) {
        console.error('Failed to initialize map:', error)
        setError(`Failed to initialize: ${error instanceof Error ? error.message : 'Unknown error'}`)
        setLoading(false)
      }
    }

    initializeMap()

    // Cleanup
    return () => {
      if (map.current) {
        console.log('Cleaning up map...')
        map.current.remove()
        map.current = null
      }
    }
  }, [])

  // Always show something visible - debug panel
  const debugPanel = (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      backgroundColor: 'white',
      padding: '15px',
      borderRadius: '8px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
      zIndex: 9999,
      fontFamily: 'Arial, sans-serif',
      fontSize: '12px',
      maxWidth: '300px',
      border: '2px solid #1976d2'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Debug Info</h4>
      <div style={{ color: '#666', lineHeight: '1.4' }}>
        <div>Loading: {loading ? 'Yes' : 'No'}</div>
        <div>Error: {error || 'None'}</div>
        <div>Warehouses: {warehouses.length}</div>
        <div>Map Loaded: {mapLoaded ? 'Yes' : 'No'}</div>
        <div>Container: {mapContainer.current ? 'Found' : 'Not found'}</div>
      </div>
    </div>
  )

  // Show error state
  if (error) {
    return (
      <>
        {debugPanel}
        <div style={{
          padding: '20px',
          fontFamily: 'Arial, sans-serif',
          minHeight: '100vh',
          backgroundColor: '#ffebee',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '10px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
            textAlign: 'center',
            maxWidth: '500px'
          }}>
            <h2 style={{ color: '#d32f2f', marginBottom: '20px' }}>Map Loading Error</h2>
            <p style={{ color: '#666', marginBottom: '20px' }}>{error}</p>
            <div style={{ marginTop: '20px' }}>
              <h3>Warehouses (List View):</h3>
              {warehouses.length > 0 ? (
                <ul style={{ textAlign: 'left', margin: '10px 0' }}>
                  {warehouses.map((warehouse) => (
                    <li key={warehouse.id} style={{ margin: '8px 0' }}>
                      <strong>{warehouse.name}</strong><br />
                      <small>Lat: {warehouse.lat}, Lon: {warehouse.lon}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No warehouse data available</p>
              )}
            </div>
            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '16px',
                marginTop: '20px'
              }}
            >
              Retry
            </button>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      {/* Always visible debug panel */}
      {debugPanel}

      {/* Global CSS reset for map */}
      <style>{`
        * {
          box-sizing: border-box;
        }
        html, body {
          margin: 0;
          padding: 0;
          height: 100%;
          width: 100%;
        }
        #root {
          height: 100vh;
          width: 100vw;
        }
        .maplibregl-map {
          font-family: 'Arial', sans-serif;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        height: '100vh',
        width: '100vw',
        overflow: 'hidden'
      }}>
        {/* Loading overlay */}
        {loading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            flexDirection: 'column'
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '30px',
              borderRadius: '10px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
              textAlign: 'center'
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                border: '4px solid #f3f3f3',
                borderTop: '4px solid #1976d2',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 20px'
              }}></div>
              <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Loading Logistics Map</h3>
              <p style={{ margin: 0, color: '#666' }}>
                {warehouses.length > 0 ? 'Initializing map...' : 'Fetching warehouse data...'}
              </p>
            </div>
          </div>
        )}

        {/* Map container with explicit dimensions */}
        <div
          ref={mapContainer}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            height: '100vh',
            width: '100vw',
            backgroundColor: '#f0f0f0',
            minHeight: '100vh',
            minWidth: '100vw',
            zIndex: 1
          }}
        />

        {/* Map info panel */}
        {mapLoaded && (
          <div style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            backgroundColor: 'white',
            padding: '15px',
            borderRadius: '8px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: 100,
            maxWidth: '300px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '16px' }}>
              Logistics POC
            </h3>
            <p style={{ margin: '0 0 10px 0', color: '#666', fontSize: '14px' }}>
              {warehouses.length} warehouse{warehouses.length !== 1 ? 's' : ''} loaded
            </p>
            <div style={{ fontSize: '12px', color: '#999' }}>
              Click markers for details
            </div>
          </div>
        )}

        {/* Map info panel */}
        {mapLoaded && (
          <div style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            backgroundColor: 'white',
            padding: '15px',
            borderRadius: '8px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: 100,
            maxWidth: '300px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '16px' }}>
              Logistics POC
            </h3>
            <p style={{ margin: '0 0 10px 0', color: '#666', fontSize: '14px' }}>
              {warehouses.length} warehouse{warehouses.length !== 1 ? 's' : ''} loaded
            </p>
            <div style={{ fontSize: '12px', color: '#999' }}>
              Click markers for details
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default App
