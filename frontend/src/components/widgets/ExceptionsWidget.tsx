/* Temporary: allow explicit any in widget until we add proper types */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Clock, Package, Route } from 'lucide-react';
import LogisticsAPI from '../../services/api';

interface ExceptionsWidgetProps {
  config: {
    type: 'Exceptions';
    kinds: string[];
  };
}

type Exception = {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  message: string;
  route_id?: string;
};

const exceptionIcons = {
  eta_risk: Clock,
  stock: Package,
  overlap: Route,
  late_order: AlertTriangle
};

const severityColors = {
  low: '#86868b',
  medium: '#ff9500',
  high: '#ff453a',
  critical: '#d70015'
};

const severityLabels = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical'
};

export const ExceptionsWidget: React.FC<ExceptionsWidgetProps> = ({ config }) => {
  const { data: exceptions, isLoading, error } = useQuery({
    queryKey: ['exceptions'],
    queryFn: LogisticsAPI.getExceptions,
    refetchInterval: 15 * 1000, // Refresh every 15 seconds for alerts
  });

  if (isLoading) {
    return (
      <div className="widget-loading">
        <div className="loading-spinner"></div>
        <span style={{ marginLeft: '0.5rem' }}>Loading alerts...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="widget-error">
        <div className="widget-error-icon">⚠️</div>
        <div>Failed to load alerts</div>
      </div>
    );
  }

  if (!exceptions || exceptions.length === 0) {
    return (
      <div className="widget-placeholder" style={{ color: '#30d158' }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
        <div>No active alerts</div>
      </div>
    );
  }

  // Filter exceptions based on config
  const filteredExceptions = exceptions.filter((exception: Exception) =>
    config.kinds.includes(exception.type)
  );

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="exceptions-widget">
      <div className="exceptions-summary">
        <div className="summary-stat">
          <div className="stat-number">{filteredExceptions.length}</div>
          <div className="stat-label">Active Alerts</div>
        </div>
        <div className="summary-breakdown">
          {Object.entries(severityLabels).map(([severity, label]) => {
            const sev = severity as keyof typeof severityLabels;
            const count = filteredExceptions.filter((exc: Exception) => exc.severity === sev).length;
            return count > 0 ? (
              <div key={severity} className="breakdown-item">
                <span
                  className="severity-dot"
                  style={{ backgroundColor: severityColors[severity as keyof typeof severityColors] }}
                />
                <span className="breakdown-count">{count}</span>
                <span className="breakdown-label">{label}</span>
              </div>
            ) : null;
          })}
        </div>
      </div>

      <div className="exceptions-list">
        {filteredExceptions.map((exception: Exception) => {
          const IconComponent = exceptionIcons[exception.type as keyof typeof exceptionIcons] || AlertTriangle;

          return (
            <div key={exception.id} className="exception-item">
              <div className="exception-header">
                <div className="exception-icon">
                  <IconComponent
                    size={16}
                    color={severityColors[exception.severity as keyof typeof severityColors]}
                  />
                </div>
                <div className="exception-meta">
                  <span
                    className="exception-severity"
                    style={{
                      color: severityColors[exception.severity as keyof typeof severityColors],
                      fontWeight: 600
                    }}
                  >
                    {severityLabels[exception.severity as keyof typeof severityLabels]}
                  </span>
                  <span className="exception-time">
                    {formatTimestamp(exception.timestamp)}
                  </span>
                </div>
              </div>

              <div className="exception-message">
                {exception.message}
              </div>

              {exception.route_id && (
                <div className="exception-context">
                  <span className="context-label">Route:</span>
                  <span className="context-value">{exception.route_id}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>


    </div>
  );
};