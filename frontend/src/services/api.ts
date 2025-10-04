import axios from "axios";
import type {
  LivePosition as SharedLivePosition,
  StockRecord,
  PlanRunRequest,
  PlanRunResponse,
  RouteSummary,
} from "./types";

// API Base Configuration
const API_BASE = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Types for API responses
export type RoutePoint = { lat: number; lon: number };

export interface Route {
  id: string;
  vehicle_id: string;
  status: "planned" | "active" | "completed" | "delayed";
  eta: string;
  utilization: number;
  stops: RoutePoint[];
  overlap_areas?: string[];
}

export interface KPIData {
  on_time_pct: number;
  overlap_pct: number;
  utilization_median: number;
  total_routes: number;
  active_trucks: number;
}

export interface Exception {
  id: string;
  type: "eta_risk" | "stock" | "overlap" | "late_order";
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  timestamp: string;
  route_id?: string;
  location?: RoutePoint;
}

export interface InventoryItem {
  sku: string;
  name: string;
  available: number;
  reserved: number;
  location: string;
}

export interface TrafficIncident {
  id: string;
  type: string;
  severity: string;
  location: RoutePoint;
  description: string;
  estimated_delay: number;
}

export interface RouteGeometryResponse {
  geometry: {
    type: "LineString";
    coordinates: Array<[number, number]>; // [lon, lat]
  };
}

export type LivePosition = SharedLivePosition; // re-export from shared types

// Internal/Raw API shapes
// Raw response shapes were used previously for mapping; backend now returns typed objects matching the frontend interfaces.

// API Service Functions
export class LogisticsAPI {
  // Routing APIs
  static async planRun(request: PlanRunRequest): Promise<PlanRunResponse> {
    const response = await api.post("/plan/run", request);
    return response.data as PlanRunResponse;
  }

  static async reRoute(request: {
    route_id: string;
    reason: string;
    priority?: "low" | "high";
  }) {
    const response = await api.post("/reroute", request);
    return response.data;
  }

  static async getKPISnapshot(): Promise<KPIData> {
    const response = await api.get("/routing/kpis");
    return {
      on_time_pct: response.data.on_time_pct,
      overlap_pct: response.data.overlap_pct,
      utilization_median: response.data.utilization_pct,
      total_routes: response.data.total_active_routes,
      active_trucks: response.data.total_active_routes,
    };
  }

  // Inventory APIs
  static async getInventorySnapshot(): Promise<InventoryItem[]> {
    const response = await api.get("/inventory/snapshot");
    // Backend returns a SnapshotResponse containing `stock` (array of StockRecord)
    // Map the backend shape to the frontend InventoryItem expected shape where possible.
    const stock: StockRecord[] = response.data.stock || [];
    return stock.map((s: StockRecord) => ({
      sku: s.item_id || "unknown",
      name: s.item_id || "unknown",
      available: s.qty || 0,
      reserved: 0,
      location: s.location_id || "",
    }));
  }

  // Generate / seed utilities
  static async generateInventory(count: number = 50) {
    const response = await api.post("/inventory/generate", { count });
    return response.data;
  }

  static async generateOrders(count: number = 5) {
    const response = await api.post("/orders/generate", { count });
    return response.data;
  }

  static async reserveInventory(request: {
    items: Array<{ sku: string; quantity: number; location: string }>;
    order_id: string;
    ttl_minutes?: number;
  }) {
    const response = await api.post("/inventory/reserve", request);
    return response.data;
  }

  static async releaseInventory(request: {
    reservation_id: string;
    reason?: string;
  }) {
    const response = await api.put("/inventory/release", request);
    return response.data;
  }

  static async getInventoryEvents(since?: string) {
    const params = since ? { since } : {};
    const response = await api.get("/inventory/events", { params });
    return response.data.events || [];
  }

  static async checkFeasibility(request: {
    items: Array<{ sku: string; quantity: number }>;
    location: string;
  }) {
    const response = await api.post("/inventory/feasibility", request);
    return response.data;
  }

  // Mock APIs for missing endpoints
  static async getActiveRoutes(): Promise<RouteSummary[]> {
    const response = await api.get("/routing/active-routes");
    return response.data as RouteSummary[];
  }

  static async getExceptions(): Promise<Exception[]> {
    const response = await api.get("/routing/exceptions");
    return response.data;
  }

  static async getTrafficIncidents(): Promise<TrafficIncident[]> {
    const response = await api.get("/routing/traffic-incidents");
    return response.data as TrafficIncident[];
  }

  static async getWarehouses() {
    try {
      const response = await api.get("/warehouses/");
      return response.data;
    } catch (error) {
      // Fallback to mock data if API is not available
      console.warn(
        "Failed to fetch warehouses from API, using mock data:",
        error,
      );
      return [
        {
          id: "warehouse-001",
          name: "Toronto Central",
          lat: 43.6532,
          lon: -79.3832,
        },
        {
          id: "warehouse-002",
          name: "Toronto East",
          lat: 43.6511,
          lon: -79.347,
        },
      ];
    }
  }

  static async getRouteGeometry(
    coords: Array<[number, number]>,
    profile: string = "driving",
  ): Promise<RouteGeometryResponse> {
    const response = await api.post("/routing/route-geometry", {
      coords,
      profile,
    });
    return response.data as RouteGeometryResponse;
  }

  static async getLivePositions(
    advance: boolean = true,
  ): Promise<LivePosition[]> {
    const response = await api.get("/routing/live-positions", {
      params: { advance },
    });
    return response.data as LivePosition[];
  }
}

export default LogisticsAPI;
