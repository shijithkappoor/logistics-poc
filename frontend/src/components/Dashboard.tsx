import React, { useEffect } from 'react';
import { defaultDashboardConfig, type DashboardConfig } from '../config/dashboard';
import { MapWidget } from './widgets/MapWidget';
import { KPIsWidget } from './widgets/KPIsWidget';
import { RoutesTableWidget } from './widgets/RoutesTableWidget';
import { ExceptionsWidget } from './widgets/ExceptionsWidget';
import './Dashboard.css';

interface DashboardProps {
	config?: DashboardConfig;
}

interface WidgetProps {
	id: string;
	title?: string;
	refreshSec?: number;
	onRemove?: (id: string) => void;
	children: React.ReactNode;
}

const WidgetContainer: React.FC<WidgetProps> = ({
	id,
	title,
	refreshSec,
	onRemove,
	children
}) => {
	useEffect(() => {
		if (refreshSec && refreshSec > 0) {
			const interval = setInterval(() => {
				// Trigger refresh by updating timestamp - widgets will handle their own refresh
				// This is mainly for visual indication that auto-refresh is working
			}, refreshSec * 1000);

			return () => clearInterval(interval);
		}
	}, [refreshSec]);

	return (
		<div className="widget-container">
			{title && (
				<div className="widget-header">
					<h3 className="widget-title">{title}</h3>
					<div className="widget-controls">
						{refreshSec && (
							<span className="refresh-indicator" title={`Auto-refresh every ${refreshSec}s`}>
								🔄
							</span>
						)}
						{onRemove && (
							<button
								className="widget-remove"
								onClick={() => onRemove(id)}
								title="Remove widget"
							>
								✕
							</button>
						)}
					</div>
				</div>
			)}
			<div className="widget-content">
				{children}
			</div>
		</div>
	);
};

export const Dashboard: React.FC<DashboardProps> = ({
	config = defaultDashboardConfig
}) => {
	return (
		<div className="dashboard">
			<div className="dashboard-header">
				<h1>Logistics Operations Dashboard</h1>
				<div className="dashboard-controls">
					<span className="status-indicator online">● Online</span>
				</div>
			</div>

			<div className="dashboard-content">
				{/* Left Half - Map */}
				<div className="dashboard-left">
					<WidgetContainer
						id="main-map"
						title="Live Operations Map"
						refreshSec={30}
					>
						<MapWidget config={config.widgets.Map} />
					</WidgetContainer>
				</div>

				{/* Right Half - Other Widgets */}
				<div className="dashboard-right">
					<div className="dashboard-right-top">
						<WidgetContainer
							id="kpis"
							title="Key Performance Indicators"
							refreshSec={30}
						>
							<KPIsWidget config={config.widgets.KPIs} />
						</WidgetContainer>

						<WidgetContainer
							id="exceptions"
							title="Active Alerts"
							refreshSec={15}
						>
							<ExceptionsWidget config={config.widgets.Exceptions} />
						</WidgetContainer>
					</div>

					<div className="dashboard-right-bottom">
						<WidgetContainer
							id="routes-table"
							title="Active Routes"
							refreshSec={30}
						>
							<RoutesTableWidget config={config.widgets.RoutesTable} />
						</WidgetContainer>
					</div>
				</div>
			</div>
		</div>
	);
};

export default Dashboard;