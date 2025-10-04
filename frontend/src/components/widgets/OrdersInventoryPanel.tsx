import React from 'react';
import { useOrders, useInventorySnapshot } from '../../services/hooks';
import type { InventoryItem } from '../../services/api';
import Resizable from '../ui/Resizable';

const panelStyle: React.CSSProperties = {
	position: 'absolute',
	right: 12,
	top: 12,
	width: 320,
	maxHeight: '60vh',
	overflow: 'auto',
	background: 'rgba(255,255,255,0.95)',
	boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
	borderRadius: 8,
	padding: 12,
	fontSize: 13,
	zIndex: 10,
};

export default function OrdersInventoryPanel() {
	const { data: orders } = useOrders();
	const { data: inventory } = useInventorySnapshot();

	const orderCount = Array.isArray(orders) ? orders.length : 0;
	const inventoryItems: InventoryItem[] = Array.isArray(inventory) ? inventory : [];

	// show top 5 SKUs by available quantity
	const topSkus = [...inventoryItems]
		.sort((a, b) => (b.available || 0) - (a.available || 0))
		.slice(0, 5);

	return (
		<Resizable initialHeight={260} minHeight={140} style={panelStyle}>
			<div aria-live="polite">
				<div style={{ fontWeight: 600, marginBottom: 8 }}>Orders & Inventory</div>
				<div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
					<div>
						<div style={{ fontSize: 12, color: '#666' }}>Open Orders</div>
						<div style={{ fontSize: 20, fontWeight: 700 }}>{orderCount}</div>
					</div>
					<div>
						<div style={{ fontSize: 12, color: '#666' }}>Inventory SKUs</div>
						<div style={{ fontSize: 20, fontWeight: 700 }}>{inventoryItems.length}</div>
					</div>
				</div>

				<div style={{ fontSize: 13, marginTop: 6 }}>
					<div style={{ color: '#666', marginBottom: 6 }}>Top SKUs</div>
					{topSkus.length === 0 ? (
						<div style={{ color: '#999' }}>No inventory data</div>
					) : (
						<ul style={{ margin: 0, paddingLeft: 16 }}>
							{topSkus.map((it) => (
								<li key={it.sku}>
									{it.sku} — <strong>{it.available ?? 0}</strong>
								</li>
							))}
						</ul>
					)}
				</div>
			</div>
		</Resizable>
	);
}
