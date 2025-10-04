import React, { useState } from 'react';

import LogisticsAPI from '../../services/api';
import { useOrders, useInventorySnapshot } from '../../services/hooks';
import { useQueryClient } from '@tanstack/react-query';
import Resizable from '../ui/Resizable';

type PlanRunRequest = { region?: string; max_trucks?: number; algorithm?: string };
type PlanRunResponse = { routes?: Array<unknown> };

type Order = { id?: string; order_id?: string; status?: string; items?: unknown[] };
type RouteSummary = { id?: string; route_id?: string; vehicle_id?: string; stops?: unknown[] };

const containerStyle: React.CSSProperties = {
	position: 'absolute',
	right: 12,
	bottom: 12,
	width: 360,
	maxHeight: '55vh',
	overflow: 'auto',
	background: 'rgba(255,255,255,0.96)',
	boxShadow: '0 2px 12px rgba(0,0,0,0.12)',
	borderRadius: 8,
	padding: 12,
	zIndex: 11,
};

export default function OrdersInventoryLiveWidget() {
	const { data: orders, isFetching: ordersFetching } = useOrders();
	const { data: inventory, isFetching: invFetching } = useInventorySnapshot();
	const [message, setMessage] = useState<string | null>(null);
	const [createdRoutes, setCreatedRoutes] = useState<unknown[]>([]);
	const [showConfirm, setShowConfirm] = useState(false);
	const [addToMap, setAddToMap] = useState(true);
	const [region, setRegion] = useState('demo');
	const [maxTrucks, setMaxTrucks] = useState(5);

	const [creating, setCreating] = useState(false);
	const queryClient = useQueryClient();

	async function createRoutesAsync(opts: PlanRunRequest) {
		setCreating(true);
		setMessage('Creating routes...');
		try {
			const data = (await LogisticsAPI.planRun(opts)) as PlanRunResponse;
			const created = data?.routes || [];
			setCreatedRoutes(created as unknown[]);
			setMessage(`Created ${created.length} routes`);

			// fetch canonical active routes from backend and update React Query cache so map follows canonical state
			try {
				const active = await LogisticsAPI.getActiveRoutes();
				queryClient.setQueryData(['routes'], active);
			} catch (err) {
				// fallback: keep createdRoutes in cache
				console.warn('Failed to refresh active routes after create', err);
			}

			// set created routes so MapWidget can react and center/pop up
			queryClient.setQueryData(['created-routes'], created);

			setTimeout(() => setMessage(null), 4000);
		} catch (err: unknown) {
			setMessage(`Failed to create routes: ${String(err)}`);
		} finally {
			setCreating(false);
		}
	}

	const onCreateRoutes = () => {
		setShowConfirm(true);
	};

	const onConfirmCreate = () => {
		setShowConfirm(false);
		void createRoutesAsync({ region, max_trucks: maxTrucks });
	};

	return (
		<Resizable initialHeight={340} minHeight={180} style={containerStyle}>
			<div role="region" aria-label="Orders and inventory live">
				<div style={{ fontWeight: 700, marginBottom: 8 }}>Live Orders & Inventory</div>
				<div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
					<div>
						<div style={{ fontSize: 12, color: '#666' }}>Open Orders</div>
						<div style={{ fontSize: 18, fontWeight: 700 }}>{Array.isArray(orders) ? orders.length : 0}</div>
						<div style={{ fontSize: 12, color: '#888' }}>{ordersFetching ? 'updating…' : 'idle'}</div>
					</div>
					<div>
						<div style={{ fontSize: 12, color: '#666' }}>Inventory SKUs</div>
						<div style={{ fontSize: 18, fontWeight: 700 }}>{Array.isArray(inventory) ? inventory.length : 0}</div>
						<div style={{ fontSize: 12, color: '#888' }}>{invFetching ? 'updating…' : 'idle'}</div>
					</div>
				</div>

				<div style={{ marginTop: 8 }}>
					<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
						<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
							<label style={{ fontSize: 12, color: '#444' }}>Region</label>
							<input value={region} onChange={(e) => setRegion(e.target.value)} style={{ width: 120, padding: 6, borderRadius: 6, border: '1px solid #ddd' }} />
							<label style={{ fontSize: 12, color: '#444' }}>Max trucks</label>
							<input type="number" value={maxTrucks} onChange={(e) => setMaxTrucks(parseInt(e.target.value || '1', 10))} style={{ width: 64, padding: 6, borderRadius: 6, border: '1px solid #ddd' }} />
						</div>
						<label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
							<input type="checkbox" checked={addToMap} onChange={(e) => setAddToMap(e.target.checked)} /> Add to map
						</label>
					</div>

					<div style={{ marginTop: 8 }}>
						<div style={{ display: 'flex', gap: 8 }}>
							<button
								onClick={async () => {
									setMessage('Generating inventory...');
									try {
										await LogisticsAPI.generateInventory(50);
										queryClient.invalidateQueries({ queryKey: ['inventory-snapshot'] });
										setMessage('Inventory generated');
									} catch (error) {
										console.warn('Generate inventory error', error);
										setMessage('Failed to generate inventory');
									}
									setTimeout(() => setMessage(null), 2500);
								}}
								style={{ padding: '8px 12px', borderRadius: 6, background: '#22c55e', color: '#fff', border: 'none', cursor: 'pointer' }}
							>
								Generate Inventory
							</button>

							<button
								onClick={async () => {
									setMessage('Generating orders...');
									try {
										await LogisticsAPI.generateOrders(5);
										queryClient.invalidateQueries({ queryKey: ['orders'] });
										setMessage('Orders generated');
									} catch (error) {
										console.warn('Generate orders error', error);
										setMessage('Failed to generate orders');
									}
									setTimeout(() => setMessage(null), 2500);
								}}
								style={{ padding: '8px 12px', borderRadius: 6, background: '#f59e0b', color: '#fff', border: 'none', cursor: 'pointer' }}
							>
								Generate Orders
							</button>

							<button
								onClick={onCreateRoutes}
								disabled={creating}
								style={{ padding: '8px 12px', borderRadius: 6, background: '#007aff', color: '#fff', border: 'none', cursor: 'pointer' }}
							>
								{creating ? 'Creating…' : 'Create Routes'}
							</button>
						</div>
					</div>
					{message && <div style={{ marginTop: 8, color: '#333' }}>{message}</div>}
				</div>

				<div style={{ marginTop: 10 }}>
					<div style={{ fontWeight: 600, marginBottom: 6 }}>Recent Orders</div>
					<ul style={{ margin: 0, paddingLeft: 16, maxHeight: 160, overflow: 'auto' }}>
						{Array.isArray(orders) && orders.length > 0 ? (
							orders.slice(0, 20).map((o: Order) => (
								<li key={o.id || o.order_id} style={{ marginBottom: 6 }}>
									<div style={{ fontSize: 13 }}><strong>{o.id || o.order_id}</strong> — {o.status ?? 'n/a'}</div>
									<div style={{ fontSize: 12, color: '#666' }}>{o.items ? `${o.items.length} items` : ''}</div>
								</li>
							))
						) : (
							<li style={{ color: '#999' }}>No orders</li>
						)}
					</ul>
				</div>
				{createdRoutes.length > 0 && (
					<div style={{ marginTop: 10 }}>
						<div style={{ fontWeight: 600, marginBottom: 6 }}>Created Routes</div>
						<ul style={{ margin: 0, paddingLeft: 16, maxHeight: 160, overflow: 'auto' }}>
							{createdRoutes.map((r) => {
								const rr = r as RouteSummary;
								return (
									<li key={rr.id || rr.route_id} style={{ marginBottom: 6 }}>
										<div style={{ fontSize: 13 }}><strong>{rr.id || rr.route_id}</strong> — vehicle: {rr.vehicle_id ?? 'n/a'}</div>
										<div style={{ fontSize: 12, color: '#666' }}>{rr.stops ? `${rr.stops.length} stops` : ''}</div>
									</li>
								);
							})}
						</ul>
					</div>
				)}

				{showConfirm && (
					<div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.4)' }}>
						<div style={{ width: 360, background: '#fff', borderRadius: 8, padding: 16 }}>
							<div style={{ fontWeight: 700, marginBottom: 8 }}>Confirm create routes</div>
							<div style={{ marginBottom: 12 }}>Create routes for region <strong>{region}</strong> with up to <strong>{maxTrucks}</strong> trucks?</div>
							<div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
								<button onClick={() => setShowConfirm(false)} style={{ padding: '8px 12px', borderRadius: 6 }}>Cancel</button>
								<button onClick={onConfirmCreate} style={{ padding: '8px 12px', borderRadius: 6, background: '#007aff', color: '#fff', border: 'none' }}>Confirm</button>
							</div>
						</div>
					</div>
				)}
			</div>
		</Resizable>
	);
}
