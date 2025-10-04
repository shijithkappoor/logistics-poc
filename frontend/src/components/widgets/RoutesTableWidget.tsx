import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, MapPin, Clock, Truck } from 'lucide-react';
import LogisticsAPI, { type Route } from '../../services/api';

interface RoutesTableWidgetProps {
	config: {
		type: 'RoutesTable';
		pageSize: number;
	};
}

const statusColors = {
	planned: '#007aff',
	active: '#30d158',
	completed: '#86868b',
	delayed: '#ff453a'
};

const statusLabels = {
	planned: 'Planned',
	active: 'Active',
	completed: 'Completed',
	delayed: 'Delayed'
};

export const RoutesTableWidget: React.FC<RoutesTableWidgetProps> = ({ config }) => {
	const [currentPage, setCurrentPage] = useState(1);

	const { data: routes, isLoading, error } = useQuery({
		queryKey: ['active-routes'],
		queryFn: LogisticsAPI.getActiveRoutes,
		refetchInterval: 30 * 1000, // Refresh every 30 seconds
	});

	if (isLoading) {
		return (
			<div className="widget-loading">
				<div className="loading-spinner"></div>
				<span style={{ marginLeft: '0.5rem' }}>Loading routes...</span>
			</div>
		);
	}

	if (error) {
		return (
			<div className="widget-error">
				<div className="widget-error-icon">🚛</div>
				<div>Failed to load routes</div>
			</div>
		);
	}

	if (!routes || routes.length === 0) {
		return (
			<div className="widget-placeholder">
				No active routes found
			</div>
		);
	}

	// Pagination logic
	const totalPages = Math.ceil(routes.length / config.pageSize);
	const startIndex = (currentPage - 1) * config.pageSize;
	const endIndex = startIndex + config.pageSize;
	const currentRoutes = routes.slice(startIndex, endIndex);

	const formatETA = (eta: string) => {
		const date = new Date(eta);
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
	};

	const formatUtilization = (utilization: number) => {
		return `${utilization.toFixed(1)}%`;
	};

	return (
		<div className="routes-table-widget">
			<div className="table-container">
				<table className="routes-table">
					<thead>
						<tr>
							<th>
								<div className="header-cell">
									<Truck size={16} />
									Vehicle
								</div>
							</th>
							<th>
								<div className="header-cell">
									Status
								</div>
							</th>
							<th>
								<div className="header-cell">
									<Clock size={16} />
									ETA
								</div>
							</th>
							<th>
								<div className="header-cell">
									Utilization
								</div>
							</th>
							<th>
								<div className="header-cell">
									<MapPin size={16} />
									Stops
								</div>
							</th>
						</tr>
					</thead>
					<tbody>
						{currentRoutes.map((route: Route) => (
							<tr key={route.id} className="route-row">
								<td>
									<div className="vehicle-cell">
										<div className="vehicle-id">{route.vehicle_id}</div>
										<div className="route-id">{route.id}</div>
									</div>
								</td>
								<td>
									<span
										className="status-badge"
										style={{
											backgroundColor: statusColors[route.status],
											color: 'white'
										}}
									>
										{statusLabels[route.status]}
									</span>
								</td>
								<td>
									<div className="eta-cell">
										{formatETA(route.eta)}
									</div>
								</td>
								<td>
									<div className="utilization-cell">
										<div className="utilization-bar">
											<div
												className="utilization-fill"
												style={{
													width: `${Math.min(route.utilization, 100)}%`,
													backgroundColor: route.utilization > 90 ? '#ff453a' :
														route.utilization > 75 ? '#ff9500' : '#30d158'
												}}
											/>
										</div>
										<span className="utilization-text">
											{formatUtilization(route.utilization)}
										</span>
									</div>
								</td>
								<td>
									<div className="stops-cell">
										{route.stops.length} stops
										{route.overlap_areas && route.overlap_areas.length > 0 && (
											<span className="overlap-indicator" title="Route has overlapping areas">
												⚠️
											</span>
										)}
									</div>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>

			{totalPages > 1 && (
				<div className="pagination">
					<button
						className="pagination-btn"
						disabled={currentPage === 1}
						onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
					>
						<ChevronLeft size={16} />
					</button>

					<span className="pagination-info">
						Page {currentPage} of {totalPages} ({routes.length} total)
					</span>

					<button
						className="pagination-btn"
						disabled={currentPage === totalPages}
						onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
					>
						<ChevronRight size={16} />
					</button>
				</div>
			)}


		</div>
	);
};