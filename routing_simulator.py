"""
Routing simulator for vehicle routing optimization with H3 integration
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field
import requests
import math

from routing_models import (
    PlanRunRequest, ReRouteRequest, PlanRunResponse, ReRouteResponse,
    RouteSummary, RouteStop, StopType, Location, OverlapIncident,
    PlanKPI, PickPackOutput, PickTask
)

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False
    print("Warning: h3 library not available. H3 cells will use mock values.")


@dataclass
class OptimizationResult:
    """Results from the routing optimization"""
    routes: List[RouteSummary]
    overlap_incidents: List[OverlapIncident]
    kpi: PlanKPI
    runtime_s: float
    # store route geometries keyed by truck_id (list of [lon, lat] coords)
    route_geometries: Dict[str, List[List[float]]] = field(default_factory=dict)


class RoutingSimulator:
    """
    Vehicle routing simulator with GTA-based routing, H3 integration, and overlap detection
    """
    
    def __init__(self):
        # GTA depot locations for realistic simulation
        self.gta_depots = {
            "depot_north": Location(lat=43.761539, lon=-79.411079),  # North York
            "depot_west": Location(lat=43.650570, lon=-79.547849),   # Etobicoke
            "depot_east": Location(lat=43.686482, lon=-79.176903),   # Scarborough
        }
        
        # Sample warehouse data for pick/pack simulation
        self.warehouse_aisles = ["A", "B", "C", "D", "E", "F"]
        self.items_per_aisle = 50
        
        # Routing optimization cache
        self._plan_cache: Dict[str, OptimizationResult] = {}
    
    def calculate_distance_km(self, loc1: Location, loc2: Location) -> float:
        """Calculate driving distance between two locations (Haversine approximation + road factor)"""
        # Haversine formula
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        straight_distance = R * c
        # Apply road factor for urban driving
        return straight_distance * 1.3
    
    def populate_h3_cells(self, stops: List[RouteStop], h3_resolution: int) -> List[RouteStop]:
        """Populate H3 cells for route stops"""
        for stop in stops:
            if H3_AVAILABLE:
                try:
                    # Try new API first
                    stop.h3 = h3.latlng_to_cell(stop.location.lat, stop.location.lon, h3_resolution)
                except AttributeError:
                    # Fall back to old API
                    try:
                        stop.h3 = h3.geo_to_h3(stop.location.lat, stop.location.lon, h3_resolution)
                    except AttributeError:
                        # Use mock if both fail
                        lat_int = int(stop.location.lat * 1000)
                        lon_int = int(stop.location.lon * 1000)
                        stop.h3 = f"8{abs(lat_int % 10000):04d}{abs(lon_int % 10000):04d}"
            else:
                # Mock H3 cell for testing without h3 library
                lat_int = int(stop.location.lat * 1000)
                lon_int = int(stop.location.lon * 1000)
                stop.h3 = f"8{abs(lat_int % 10000):04d}{abs(lon_int % 10000):04d}"
        return stops
    
    def detect_overlaps(self, routes: List[RouteSummary], window_minutes: int = 30) -> List[OverlapIncident]:
        """Detect spatial-temporal overlaps between trucks"""
        overlaps = []
        
        # Group stops by H3 cell
        h3_timeline: Dict[str, List[Tuple[str, datetime, datetime]]] = {}
        
        for route in routes:
            for stop in route.stops:
                if stop.h3 and stop.type != StopType.DEPOT:
                    service_end = stop.eta + timedelta(minutes=stop.service_min)
                    
                    if stop.h3 not in h3_timeline:
                        h3_timeline[stop.h3] = []
                    h3_timeline[stop.h3].append((route.truck_id, stop.eta, service_end))
        
        # Find overlapping time windows in same H3 cells
        for h3_cell, timeline in h3_timeline.items():
            timeline.sort(key=lambda x: x[1])  # Sort by start time
            
            for i in range(len(timeline)):
                overlapping_trucks = [timeline[i][0]]
                overlap_start = timeline[i][1]
                overlap_end = timeline[i][2]
                
                for j in range(i + 1, len(timeline)):
                    # Check if trucks overlap within the window
                    if timeline[j][1] <= overlap_end + timedelta(minutes=window_minutes):
                        overlapping_trucks.append(timeline[j][0])
                        overlap_end = max(overlap_end, timeline[j][2])
                    else:
                        break
                
                if len(overlapping_trucks) >= 2:
                    overlaps.append(OverlapIncident(
                        h3=h3_cell,
                        start_ts=overlap_start,
                        end_ts=overlap_end,
                        truck_ids=overlapping_trucks
                    ))
        
        return overlaps
    
    def calculate_utilization(self, route: RouteSummary, truck_capacity: float) -> float:
        """Calculate volume-based utilization: sum(load_cuft)/capacity_cuft"""
        total_load = sum(stop.load_cuft for stop in route.stops if stop.type == StopType.DELIVERY)
        return min(total_load / truck_capacity, 1.0) if truck_capacity > 0 else 0.0
    
    def generate_pick_sequence(self, route: RouteSummary) -> PickPackOutput:
        """Generate pick sequence and loading order for a route"""
        pick_tasks = []
        delivery_stops = [stop for stop in route.stops if stop.type == StopType.DELIVERY]
        
        # Generate pick tasks based on stops
        seq = 1
        for stop in delivery_stops:
            # Simulate items for this stop
            num_items = max(1, int(stop.load_cuft / 5))  # Roughly 5 cuft per item
            for item_idx in range(num_items):
                aisle = random.choice(self.warehouse_aisles)
                bin_num = random.randint(1, self.items_per_aisle)
                
                pick_tasks.append(PickTask(
                    seq=seq,
                    aisle=aisle,
                    bin=f"{bin_num:02d}",
                    item_id=f"ITEM_{stop.stop_id}_{item_idx+1}",
                    qty=random.uniform(1, 3)
                ))
                seq += 1
        
        # Loading order: reverse of delivery sequence (LIFO)
        loading_order = [stop.stop_id for stop in reversed(delivery_stops)]
        
        return PickPackOutput(
            truck_id=route.truck_id,
            pick_sequence=pick_tasks,
            loading_order=loading_order
        )
    
    def optimize_routes(self, request: PlanRunRequest) -> OptimizationResult:
        """Main routing optimization engine"""
        start_time = datetime.now()
        
        # Basic nearest neighbor routing with some optimizations
        routes = []
        
        # Group stops by depot proximity for initial assignment
        depot_assignments = self._assign_stops_to_depots(request.stops, request.depots)
        
        for truck in request.trucks:
            truck_depot = next(d for d in request.depots if d.id == truck.depot_id)
            assigned_stops = depot_assignments.get(truck.depot_id, [])
            
            if not assigned_stops:
                continue
            
            # Create route for this truck
            route_stops = []
            current_location = truck_depot.location
            remaining_stops = assigned_stops.copy()
            current_load = 0.0
            current_time = datetime.fromisoformat(f"{request.for_date}T{request.params.delivery_window_start}:00")
            
            # Add depot start
            route_stops.append(RouteStop(
                stop_id=f"depot_start_{truck.id}",
                type=StopType.DEPOT,
                location=truck_depot.location,
                eta=current_time,
                service_min=0,
                load_cuft=0
            ))
            
            total_distance = 0.0
            total_drive_time = 0.0
            
            # Nearest neighbor routing
            while remaining_stops and current_load < truck.capacity_cuft:
                # Find nearest unvisited stop
                nearest_stop = min(remaining_stops, 
                                 key=lambda s: self.calculate_distance_km(current_location, s.location))
                
                # Check capacity constraint
                if current_load + nearest_stop.items_volume_cuft > truck.capacity_cuft:
                    break
                
                remaining_stops.remove(nearest_stop)
                
                # Calculate travel time and distance
                distance = self.calculate_distance_km(current_location, nearest_stop.location)
                drive_time = distance * random.uniform(1.2, 2.0)  # Variable speed
                
                total_distance += distance
                total_drive_time += drive_time
                current_time += timedelta(minutes=drive_time)
                current_load += nearest_stop.items_volume_cuft
                
                # Add route stop
                route_stops.append(RouteStop(
                    stop_id=nearest_stop.order_id,
                    type=StopType.DELIVERY,
                    location=nearest_stop.location,
                    eta=current_time,
                    eta_ci_low_min=random.uniform(5, 15),
                    eta_ci_high_min=random.uniform(15, 30),
                    service_min=nearest_stop.service_min,
                    load_cuft=nearest_stop.items_volume_cuft
                ))
                
                current_location = nearest_stop.location
                current_time += timedelta(minutes=nearest_stop.service_min)
            
            # Return to depot
            if route_stops:
                depot_distance = self.calculate_distance_km(current_location, truck_depot.location)
                depot_drive_time = depot_distance * 1.5
                total_distance += depot_distance
                total_drive_time += depot_drive_time
                current_time += timedelta(minutes=depot_drive_time)
                
                route_stops.append(RouteStop(
                    stop_id=f"depot_end_{truck.id}",
                    type=StopType.DEPOT,
                    location=truck_depot.location,
                    eta=current_time,
                    service_min=0,
                    load_cuft=0
                ))
                
                # Populate H3 cells
                route_stops = self.populate_h3_cells(route_stops, request.params.overlap_h3_res)

                # Calculate utilization
                utilization = self.calculate_utilization(
                    RouteSummary(truck_id=truck.id, stops=route_stops, distance_km=total_distance, 
                               drive_time_min=total_drive_time, utilization_pct=0), 
                    truck.capacity_cuft
                )
                
                routes.append(RouteSummary(
                    truck_id=truck.id,
                    stops=route_stops,
                    distance_km=total_distance,
                    drive_time_min=total_drive_time,
                    utilization_pct=utilization
                ))

        # Attempt to fetch route geometries via local OSRM for each generated route
        route_geometries: Dict[str, List[List[float]]] = {}
        for r in routes:
            try:
                coords = ";".join([f"{s.location.lon},{s.location.lat}" for s in r.stops])
                osrm_url = f"http://127.0.0.1:5000/route/v1/driving/{coords}"
                resp = requests.get(osrm_url, params={'overview': 'full', 'geometries': 'geojson'}, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('routes') and data['routes'][0].get('geometry'):
                        geom_coords = data['routes'][0]['geometry']['coordinates']
                        # store as [[lon, lat], ...]
                        route_geometries[r.truck_id] = geom_coords
                        continue
            except Exception:
                pass

            # fallback: straight line between stops
            route_geometries[r.truck_id] = [[s.location.lon, s.location.lat] for s in r.stops]
        
        # Detect overlaps
        overlap_incidents = self.detect_overlaps(routes)
        
        # Calculate KPIs
        total_stops = sum(len([s for s in route.stops if s.type == StopType.DELIVERY]) for route in routes)
        on_time_stops = int(total_stops * random.uniform(0.85, 0.95))  # Simulate on-time performance
        
        kpi = PlanKPI(
            on_time_pct=on_time_stops / total_stops if total_stops > 0 else 0,
            overlap_pct=len(overlap_incidents) / max(total_stops, 1),
            miles_per_order=sum(r.distance_km for r in routes) * 0.621371 / max(total_stops, 1),  # Convert km to miles
            runtime_s=(datetime.now() - start_time).total_seconds()
        )
        
        return OptimizationResult(
            routes=routes,
            overlap_incidents=overlap_incidents,
            kpi=kpi,
            runtime_s=kpi.runtime_s,
            route_geometries=route_geometries
        )
    
    def _assign_stops_to_depots(self, stops: List, depots: List) -> Dict[str, List]:
        """Assign stops to nearest depots"""
        assignments = {depot.id: [] for depot in depots}
        
        for stop in stops:
            nearest_depot = min(depots, 
                              key=lambda d: self.calculate_distance_km(stop.location, d.location))
            assignments[nearest_depot.id].append(stop)
        
        return assignments
    
    def plan_routes(self, request: PlanRunRequest) -> PlanRunResponse:
        """Execute route planning"""
        result = self.optimize_routes(request)
        
        # Generate pick/pack outputs
        pickpack = [self.generate_pick_sequence(route) for route in result.routes]
        
        plan_id = str(uuid.uuid4())
        self._plan_cache[plan_id] = result
        
        return PlanRunResponse(
            plan_id=plan_id,
            runtime_s=result.runtime_s,
            routes=result.routes,
            overlap_incidents=result.overlap_incidents,
            kpi=result.kpi,
            pickpack=pickpack
        )
    
    def reroute(self, request: ReRouteRequest) -> ReRouteResponse:
        """Execute re-routing with change tracking"""
        # Get original plan
        if request.plan_id not in self._plan_cache:
            raise ValueError(f"Plan {request.plan_id} not found")
        
        original_result = self._plan_cache[request.plan_id]
        
        # Simulate re-routing by modifying existing routes
        new_routes = []
        total_stops = 0
        changed_stops = 0
        
        for route in original_result.routes:
            if request.scope == "truck" and route.truck_id != request.truck_id:
                # Keep route unchanged if not in scope
                new_routes.append(route)
                delivery_stops = [s for s in route.stops if s.type == StopType.DELIVERY]
                total_stops += len(delivery_stops)
                continue
            
            # Apply limited changes based on change_limit
            delivery_stops = [s for s in route.stops if s.type == StopType.DELIVERY]
            total_stops += len(delivery_stops)
            
            max_changes = int(len(delivery_stops) * request.change_limit)
            actual_changes = random.randint(0, max_changes)
            changed_stops += actual_changes
            
            # Simulate route changes by slightly adjusting ETAs and sequence
            modified_stops = route.stops.copy()
            for i in range(actual_changes):
                if i < len(delivery_stops):
                    # Simulate ETA adjustment
                    stop_idx = next((j for j, s in enumerate(modified_stops) if s.stop_id == delivery_stops[i].stop_id), -1)
                    if stop_idx >= 0:
                        modified_stops[stop_idx].eta += timedelta(minutes=random.randint(-15, 15))
            
            new_routes.append(RouteSummary(
                truck_id=route.truck_id,
                stops=modified_stops,
                distance_km=route.distance_km * random.uniform(0.95, 1.05),
                drive_time_min=route.drive_time_min * random.uniform(0.95, 1.05),
                utilization_pct=route.utilization_pct
            ))
        
        # Detect new overlaps
        overlap_incidents = self.detect_overlaps(new_routes)
        
        # Update KPIs
        changed_stops_pct = changed_stops / max(total_stops, 1)
        
        kpi = PlanKPI(
            on_time_pct=original_result.kpi.on_time_pct * random.uniform(0.9, 1.0),
            overlap_pct=len(overlap_incidents) / max(total_stops, 1),
            miles_per_order=sum(r.distance_km for r in new_routes) * 0.621371 / max(total_stops, 1),
            runtime_s=random.uniform(1, 5)  # Re-routing is faster
        )
        
        return ReRouteResponse(
            plan_id=request.plan_id,
            changed_stops_pct=changed_stops_pct,
            runtime_s=kpi.runtime_s,
            routes=new_routes,
            overlap_incidents=overlap_incidents,
            kpi=kpi
        )