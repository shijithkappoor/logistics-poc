// Shared TypeScript types for frontend API shapes that mirror backend Pydantic models

export type Location = { lat: number; lon: number };

export type LivePosition = {
  vehicle_id: string;
  lat: number;
  lon: number;
  last_update?: string; // ISO timestamp (backend adds 'Z')
};

// Order stop (input) used by planner
export type OrderStop = {
  order_id: string;
  franchisee_id: string;
  location: Location;
  items_volume_cuft: number;
  service_min?: number;
  window_start?: string; // HH:MM
  window_end?: string; // HH:MM
  non_substitutable_present?: boolean;
};

export type Depot = { id: string; location: Location };

export type TruckSpec = { id: string; depot_id: string; capacity_cuft: number };

export type RoutingParams = {
  delivery_window_start?: string;
  delivery_window_end?: string;
  service_time_min?: number;
  overlap_h3_res?: number;
  avoid_overlap_weight?: number;
  unused_truck_weight?: number;
  change_cost_weight?: number;
  max_change_ratio?: number;
};

export type PlanRunRequest = {
  for_date: string; // YYYY-MM-DD
  depots: Depot[];
  trucks: TruckSpec[];
  stops: OrderStop[];
  params?: RoutingParams;
  traffic_profile_id?: string | null;
};

export type StopType = "delivery" | "pickup" | "depot";

export type RouteStop = {
  stop_id: string;
  type: StopType;
  location: Location;
  eta: string; // ISO timestamp
  eta_ci_low_min?: number | null;
  eta_ci_high_min?: number | null;
  service_min: number;
  load_cuft: number;
  h3?: string | null;
};

export type RouteSummary = {
  truck_id: string;
  stops: RouteStop[];
  distance_km: number;
  drive_time_min: number;
  utilization_pct: number; // 0..1
};

export type OverlapIncident = {
  h3: string;
  start_ts: string;
  end_ts: string;
  truck_ids: string[];
};

export type PlanKPI = {
  on_time_pct: number;
  overlap_pct: number;
  miles_per_order: number;
  runtime_s?: number | null;
};

export type PlanRunResponse = {
  plan_id: string;
  runtime_s: number;
  routes: RouteSummary[];
  overlap_incidents: OverlapIncident[];
  kpi: PlanKPI;
  pickpack: unknown[];
};

// Inventory types
export type LocationType = "warehouse" | "franchisee";

export type StockRecord = {
  location_type: LocationType;
  location_id: string;
  item_id: string;
  qty: number;
};

export type ReservationRecord = {
  reservation_id: string;
  warehouse_id: string;
  order_id: string;
  item_id: string;
  qty: number;
  ts: string; // ISO
  expires_ts?: string | null;
};

export type SnapshotResponse = {
  server_ts: string;
  stock: StockRecord[];
  reservations?: ReservationRecord[] | null;
};
