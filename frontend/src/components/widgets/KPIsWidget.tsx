/* Temporary: allow explicit any in widget until we add proper types */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import LogisticsAPI from '../../services/api';

interface KPIsWidgetProps {
	config: {
		type: 'KPIs';
		metrics: Array<{
			id: string;
			label: string;
			source: string;
			format: string;
		}>;
	};
}

interface KPICardProps {
	label: string;
	value: number;
	format: string;
	trend?: number;
}

const KPICard: React.FC<KPICardProps> = ({ label, value, format, trend }) => {
	const formatValue = (val: number, fmt: string) => {
		switch (fmt) {
			case 'pct':
				return `${val.toFixed(1)}%`;
			case 'int':
				return Math.round(val).toString();
			case 'float':
				return val.toFixed(2);
			case 'duration':
				return `${Math.round(val)}min`;
			default:
				return val.toString();
		}
	};

	const getTrendIcon = (trendValue?: number) => {
		if (!trendValue) return null;
		if (trendValue > 0) return <span className="trend-up">↗</span>;
		if (trendValue < 0) return <span className="trend-down">↘</span>;
		return <span className="trend-flat">→</span>;
	};

	return (
		<div className="kpi-card">
			<div className="kpi-label">{label}</div>
			<div className="kpi-value">
				{formatValue(value, format)}
				{getTrendIcon(trend)}
			</div>
		</div>
	);
};

export const KPIsWidget: React.FC<KPIsWidgetProps> = ({ config }) => {
	const { data: kpiData, isLoading, error } = useQuery({
		queryKey: ['kpi-snapshot'],
		queryFn: LogisticsAPI.getKPISnapshot,
		refetchInterval: 30 * 1000, // Refresh every 30 seconds
	});

	if (isLoading) {
		return (
			<div className="widget-loading">
				<div className="loading-spinner"></div>
				<span style={{ marginLeft: '0.5rem' }}>Loading KPIs...</span>
			</div>
		);
	}

	if (error) {
		return (
			<div className="widget-error">
				<div className="widget-error-icon">📊</div>
				<div>Failed to load KPIs</div>
			</div>
		);
	}

	if (!kpiData) {
		return (
			<div className="widget-placeholder">
				No KPI data available
			</div>
		);
	}

	// Prepare chart data
	const chartData = config.metrics.map(metric => ({
		name: metric.label,
		value: (kpiData as any)[metric.id] || 0,
	}));

	return (
		<div className="kpis-widget">
			<div className="kpi-cards">
				{config.metrics.map(metric => (
					<KPICard
						key={metric.id}
						label={metric.label}
						value={(kpiData as any)[metric.id] || 0}
						format={metric.format}
					/>
				))}
			</div>

			<div className="kpi-chart">
				<ResponsiveContainer width="100%" height={120}>
					<BarChart data={chartData}>
						<XAxis
							dataKey="name"
							fontSize={12}
							tick={{ fill: '#86868b' }}
							axisLine={false}
							tickLine={false}
						/>
						<YAxis hide />
						<Bar
							dataKey="value"
							fill="#007aff"
							radius={[2, 2, 0, 0]}
						/>
					</BarChart>
				</ResponsiveContainer>
			</div>

			<div className="kpi-summary">
				<div className="summary-item">
					<span className="summary-label">Total Routes:</span>
					<span className="summary-value">{kpiData.total_routes}</span>
				</div>
				<div className="summary-item">
					<span className="summary-label">Active Trucks:</span>
					<span className="summary-value">{kpiData.active_trucks}</span>
				</div>
			</div>


		</div>
	);
};