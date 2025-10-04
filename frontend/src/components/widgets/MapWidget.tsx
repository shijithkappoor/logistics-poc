import React, { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import OrdersInventoryPanel from './OrdersInventoryPanel';
import OrdersInventoryLiveWidget from './OrdersInventoryLiveWidget';
import LogisticsAPI from '../../services/api';
import type { LivePosition } from '../../services/api';

interface MapWidgetProps {
	config: {
		type: 'Map';
		center: [number, number];
		zoom: number;
		layers: Array<{ id: string; kind: string; visible: boolean }>;
	};
}

// Map widget: renders warehouses, route polylines (backend geometries) and live truck markers.
export const MapWidget: React.FC<MapWidgetProps> = ({ config }) => {
	const mapContainer = useRef<HTMLDivElement | null>(null);
	const mapRef = useRef<maplibregl.Map | null>(null);
	const markersRef = useRef<Record<string, maplibregl.Marker>>({});
	const [loaded, setLoaded] = useState(false);

	// Initialize map once
	useEffect(() => {
		if (!mapContainer.current || mapRef.current) return;

		const map = new maplibregl.Map({
			container: mapContainer.current,
			style: 'https://demotiles.maplibre.org/style.json',
			center: [config.center[1], config.center[0]] as [number, number], // [lon, lat]
			zoom: config.zoom,
		});

		map.addControl(new maplibregl.NavigationControl(), 'top-right');

		map.on('load', () => {
			mapRef.current = map;
			setLoaded(true);
		});

		return () => {
			try {
				map.remove();
			} catch (removeErr) {
				console.warn('Failed to remove map instance', removeErr);
			}
			mapRef.current = null;
		};
	}, [config.center, config.zoom]);

	// Fetch and render active routes as polylines (use backend geometry endpoint)
	useEffect(() => {
		if (!loaded || !mapRef.current) return;

		let cancelled = false;
		const map = mapRef.current;

		async function loadRoutes() {
			try {
				const routes = await LogisticsAPI.getActiveRoutes();

				// For each route, request geometry from backend using stops coordinates
				await Promise.all(
					routes.map(async (r, idx) => {
						const layerId = `route-line-${r.id || idx}`;

						// Build coords as [lon, lat] pairs
						const stops = (r.stops || []) as Array<{ lat: number; lon: number }>;
						const coords: Array<[number, number]> = stops.map((s) => [s.lon, s.lat]);

						if (coords.length < 2) return;

						// Ask backend for a routed geometry; backend will fallback to straight lines
						const geomResp = await LogisticsAPI.getRouteGeometry(coords);
						if (cancelled) return;

						const feature: GeoJSON.FeatureCollection = {
							type: 'FeatureCollection',
							features: [
								{
									type: 'Feature',
									properties: { routeId: r.id },
									geometry: geomResp.geometry as GeoJSON.Geometry,
								},
							],
						};

						// Remove existing source/layer if present
						if (map.getLayer(layerId)) {
							try {
								map.removeLayer(layerId);
							} catch (removeErr) {
								console.warn('Failed to remove existing layer', removeErr);
							}
						}
						if (map.getSource(layerId)) {
							try {
								map.removeSource(layerId);
							} catch (removeErr) {
								console.warn('Failed to remove existing source', removeErr);
							}
						}

						map.addSource(layerId, { type: 'geojson', data: feature });
						map.addLayer({
							id: layerId,
							type: 'line',
							source: layerId,
							layout: { 'line-join': 'round', 'line-cap': 'round' },
							paint: { 'line-color': '#007aff', 'line-width': 4, 'line-opacity': 0.9 },
						});
					}),
				);
			} catch (err) {
				console.warn('Failed to load routes', err);
			}
		}

		void loadRoutes();

		return () => {
			cancelled = true;
		};
	}, [loaded]);

	// Poll live positions and update markers
	useEffect(() => {
		if (!mapRef.current) return;
		let mounted = true;

		async function poll() {
			try {
				const positions: LivePosition[] = await LogisticsAPI.getLivePositions(true);
				if (!mounted || !mapRef.current) return;

				positions.forEach((p) => {
					const id = p.vehicle_id;
					const lngLat: [number, number] = [p.lon, p.lat];

					let marker = markersRef.current[id];
					if (!marker) {
						const el = document.createElement('div');
						el.style.width = '18px';
						el.style.height = '18px';
						el.style.borderRadius = '50%';
						el.style.background = '#ef4444';
						el.style.border = '2px solid #fff';
						el.style.boxShadow = '0 1px 4px rgba(0,0,0,0.4)';

						marker = new maplibregl.Marker({ element: el }).setLngLat(lngLat).addTo(mapRef.current!);
						markersRef.current[id] = marker;
					} else {
						// smooth move
						marker.setLngLat(lngLat);
					}
				});
			} catch (pollErr) {
				console.warn('Live positions poll failed', pollErr);
			}
		}

		const interval = window.setInterval(() => {
			void poll();
		}, 2000);

		// initial fetch
		void poll();

		return () => {
			mounted = false;
			clearInterval(interval);
			// remove markers
			Object.values(markersRef.current).forEach((m) => m.remove());
			markersRef.current = {};
		};
	}, []);

	return (
		<div style={{ height: '100%', width: '100%', position: 'relative' }}>
			<div ref={mapContainer} style={{ height: '100%', width: '100%' }} />
			<OrdersInventoryPanel />
			<OrdersInventoryLiveWidget />
		</div>
	);
};