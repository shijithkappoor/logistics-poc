import { useQuery } from "@tanstack/react-query";
import LogisticsAPI from "./api";

declare global {
  interface Window {
    __env?: { API_BASE?: string };
  }
}

export function useOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: async () => {
      try {
        const apiBase = window.__env?.API_BASE || "http://localhost:8000";
        const resp = await fetch(`${apiBase}/orders`);
        return resp.ok ? resp.json() : [];
      } catch (err) {
        console.warn("Failed to fetch orders", err);
        return [];
      }
    },
    refetchInterval: 30 * 1000,
  });
}

export function useInventorySnapshot() {
  return useQuery({
    queryKey: ["inventory-snapshot"],
    queryFn: () => LogisticsAPI.getInventorySnapshot(),
    refetchInterval: 30 * 1000,
  });
}
