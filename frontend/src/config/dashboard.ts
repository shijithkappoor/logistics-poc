export interface DashboardConfig {
  version: string;
  roles: string[];
  datasources: {
    apiBase: string;
    telemetryWS: string;
    routes: {
      planRun: string;
      reRoute: string;
      kpiSnapshot: string;
    };
    orders: {
      generate: string;
      list: string;
      get: string;
    };
    traffic: {
      snapshot: string;
      incidents: string;
    };
    inventory: {
      snapshot: string;
      reserve: string;
      release: string;
      events: string;
      feasibility: string;
    };
  };
  layout: {
    grid: {
      columns: number;
      rowHeight: number;
      gap: number;
    };
    panels: Array<{
      id: string;
      widget: string;
      title?: string;
      x: number;
      y: number;
      w: number;
      h: number;
      roles?: string[];
      refreshSec?: number;
      props?: Record<string, unknown>;
    }>;
  };
  widgets: {
    Map: {
      type: "Map";
      center: [number, number];
      zoom: number;
      layers: Array<{
        id: string;
        kind: string;
        visible: boolean;
        style?: Record<string, unknown>;
      }>;
    };
    KPIs: {
      type: "KPIs";
      metrics: Array<{
        id: string;
        label: string;
        source: string;
        format: string;
      }>;
    };
    RoutesTable: {
      type: "RoutesTable";
      pageSize: number;
    };
    Exceptions: {
      type: "Exceptions";
      kinds: string[];
    };
  };
}

export const defaultDashboardConfig: DashboardConfig = {
  version: "1.0.0",
  roles: ["ops", "warehouse", "admin"],
  datasources: {
    apiBase: "http://localhost:8000",
    telemetryWS: "ws://localhost:8000/stream/telemetry",
    routes: {
      planRun: "/plan/run",
      reRoute: "/reroute",
      kpiSnapshot: "/kpi/snapshot",
    },
    orders: {
      generate: "/orders/generate",
      list: "/orders",
      get: "/orders/{id}",
    },
    traffic: {
      snapshot: "/traffic/snapshot",
      incidents: "/traffic/incidents",
    },
    inventory: {
      snapshot: "/inventory/snapshot",
      reserve: "/inventory/reserve",
      release: "/inventory/release",
      events: "/inventory/events",
      feasibility: "/inventory/feasibility",
    },
  },
  layout: {
    grid: {
      columns: 12,
      rowHeight: 80,
      gap: 8,
    },
    panels: [
      {
        id: "main-map",
        widget: "Map",
        title: "Live Operations Map",
        x: 0,
        y: 0,
        w: 8,
        h: 6,
        refreshSec: 30,
      },
      {
        id: "kpis",
        widget: "KPIs",
        title: "Key Performance Indicators",
        x: 8,
        y: 0,
        w: 4,
        h: 3,
        refreshSec: 30,
      },
      {
        id: "exceptions",
        widget: "Exceptions",
        title: "Active Alerts",
        x: 8,
        y: 3,
        w: 4,
        h: 3,
        refreshSec: 15,
      },
      {
        id: "routes-table",
        widget: "RoutesTable",
        title: "Active Routes",
        x: 0,
        y: 6,
        w: 12,
        h: 4,
        refreshSec: 30,
      },
    ],
  },
  widgets: {
    Map: {
      type: "Map",
      center: [-79.3832, 43.6532],
      zoom: 9,
      layers: [
        { id: "warehouses", kind: "warehouses", visible: true },
        { id: "trucks", kind: "trucks", visible: true },
        { id: "trails", kind: "trails", visible: false },
        { id: "traffic", kind: "traffic", visible: false },
      ],
    },
    KPIs: {
      type: "KPIs",
      metrics: [
        {
          id: "on_time_pct",
          label: "On-time %",
          source: "kpiSnapshot",
          format: "pct",
        },
        {
          id: "overlap_pct",
          label: "Overlap %",
          source: "kpiSnapshot",
          format: "pct",
        },
        {
          id: "utilization_median",
          label: "Utilization (p50)",
          source: "kpiSnapshot",
          format: "pct",
        },
      ],
    },
    RoutesTable: {
      type: "RoutesTable",
      pageSize: 20,
    },
    Exceptions: {
      type: "Exceptions",
      kinds: ["eta_risk", "stock", "overlap"],
    },
  },
};
