"""Warehouse discovery utilities for auto-selecting SQL warehouses."""

from typing import Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import EndpointInfoWarehouseType


class WarehouseDiscovery:
    """Auto-discover and recommend SQL warehouses."""

    def __init__(self, workspace_client: WorkspaceClient):
        self.client = workspace_client

    def list_available_warehouses(self) -> list[dict]:
        """List all available warehouses (RUNNING or STOPPED).

        Returns:
            List of warehouse info dicts with id, name, state, and cluster_size.
        """
        warehouses = []
        for warehouse in self.client.warehouses.list():
            # Filter for SQL warehouses only (not classic)
            if warehouse.warehouse_type == EndpointInfoWarehouseType.PRO:
                warehouses.append({
                    "id": warehouse.id,
                    "name": warehouse.name,
                    "state": warehouse.state.value if warehouse.state else "UNKNOWN",
                    "cluster_size": warehouse.cluster_size if warehouse.cluster_size else "Unknown",
                })
        return warehouses

    def get_recommended_warehouse(self, purpose: str = "development") -> Optional[str]:
        """Auto-select warehouse based on purpose.

        Args:
            purpose: Either "development" or "production". Development prefers
                    smaller warehouses, production prefers larger ones.

        Returns:
            Warehouse ID or None if no suitable warehouse found.

        Selection logic:
        1. Prefer RUNNING warehouses to avoid cold start delays
        2. For development: prefer X-Small/Small clusters
        3. For production: prefer Medium/Large clusters
        4. Fallback: return first available warehouse
        """
        warehouses = self.list_available_warehouses()
        if not warehouses:
            return None

        # Separate RUNNING and other states
        running = [w for w in warehouses if w["state"] == "RUNNING"]
        other = [w for w in warehouses if w["state"] != "RUNNING"]

        # Try RUNNING warehouses first
        candidates = running if running else other

        if purpose == "development":
            # Prefer X-Small or Small for dev work
            for size in ["2X-Small", "X-Small", "Small"]:
                for w in candidates:
                    if size.lower() in w["cluster_size"].lower():
                        return w["id"]

        elif purpose == "production":
            # Prefer Medium or Large for prod work
            for size in ["Large", "Medium"]:
                for w in candidates:
                    if size.lower() in w["cluster_size"].lower():
                        return w["id"]

        # Fallback: return first available warehouse
        return candidates[0]["id"] if candidates else None

    def get_warehouse_info(self, warehouse_id: str) -> Optional[dict]:
        """Get detailed info for a specific warehouse.

        Args:
            warehouse_id: The warehouse ID to look up.

        Returns:
            Warehouse info dict or None if not found.
        """
        try:
            warehouse = self.client.warehouses.get(warehouse_id)
            return {
                "id": warehouse.id,
                "name": warehouse.name,
                "state": warehouse.state.value if warehouse.state else "UNKNOWN",
                "cluster_size": warehouse.cluster_size if warehouse.cluster_size else "Unknown",
            }
        except Exception:
            return None
