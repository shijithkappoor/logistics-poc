import React from 'react';

interface SimpleMapWidgetProps {
	config: {
		type: 'Map';
		center: [number, number];
		zoom: number;
		layers: Array<{
			id: string;
			kind: string;
			visible: boolean;
			style?: Record<string, unknown>;
		}>;
	};
}

export const SimpleMapWidget: React.FC<SimpleMapWidgetProps> = ({ config }) => {
	return (
		<div style={{
			height: '100%',
			width: '100%',
			background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
			position: 'relative',
			borderRadius: '8px',
			overflow: 'hidden'
		}}>
			{/* Map placeholder content */}
			<div style={{
				position: 'absolute',
				top: '20px',
				left: '20px',
				background: 'rgba(255,255,255,0.9)',
				padding: '12px',
				borderRadius: '6px',
				boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
			}}>
				<div style={{ fontSize: '18px', marginBottom: '4px' }}>🗺️ Live Operations Map</div>
				<div style={{ fontSize: '14px', color: '#666' }}>
					Center: {config.center[1].toFixed(4)}, {config.center[0].toFixed(4)}<br />
					Zoom: {config.zoom}
				</div>
			</div>

			{/* Mock warehouse markers */}
			<div style={{
				position: 'absolute',
				top: '45%',
				left: '40%',
				width: '12px',
				height: '12px',
				background: '#ff6b35',
				borderRadius: '50%',
				border: '2px solid white',
				boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
			}} title="Toronto Central Warehouse" />

			<div style={{
				position: 'absolute',
				top: '55%',
				left: '60%',
				width: '12px',
				height: '12px',
				background: '#ff6b35',
				borderRadius: '50%',
				border: '2px solid white',
				boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
			}} title="Toronto East Warehouse" />

			{/* Mock truck markers */}
			<div style={{
				position: 'absolute',
				top: '40%',
				left: '35%',
				fontSize: '16px'
			}}>🚛</div>

			<div style={{
				position: 'absolute',
				top: '60%',
				left: '45%',
				fontSize: '16px'
			}}>🚛</div>

			<div style={{
				position: 'absolute',
				top: '50%',
				left: '65%',
				fontSize: '16px'
			}}>🚛</div>

			{/* Mock route lines */}
			<svg style={{
				position: 'absolute',
				top: 0,
				left: 0,
				width: '100%',
				height: '100%',
				pointerEvents: 'none'
			}}>
				<path
					d="M 35% 40% Q 50% 30% 65% 50%"
					stroke="#4CAF50"
					strokeWidth="3"
					fill="none"
					strokeDasharray="5,5"
				/>
				<path
					d="M 40% 45% Q 55% 60% 70% 45%"
					stroke="#2196F3"
					strokeWidth="3"
					fill="none"
				/>
			</svg>

			{/* Legend */}
			<div style={{
				position: 'absolute',
				bottom: '20px',
				right: '20px',
				background: 'rgba(255,255,255,0.9)',
				padding: '12px',
				borderRadius: '6px',
				boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
				fontSize: '12px'
			}}>
				<div>🚛 Active Trucks</div>
				<div>⚫ Warehouses</div>
				<div style={{ color: '#4CAF50' }}>— Active Routes</div>
				<div style={{ color: '#2196F3' }}>— Planned Routes</div>
			</div>
		</div>
	);
};