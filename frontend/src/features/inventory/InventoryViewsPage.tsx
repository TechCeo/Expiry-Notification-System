import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { Batch, Location, Page, Product } from "../../api/generated/client";
import { useOrganization } from "../../shared/organization/OrganizationContext";
import { ErrorState, LoadingState } from "../../shared/ui/State";
import { BatchTable } from "./BatchesPage";

export function InventoryViewsPage() {
  const { selectedOrganizationId, canManageInventory } = useOrganization();
  const today = new Date();
  const todayIso = today.toISOString().slice(0, 10);
  const soon = new Date(today);
  soon.setDate(today.getDate() + 30);
  const soonIso = soon.toISOString().slice(0, 10);

  const products = useQuery({
    queryKey: ["view-products", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Product>>("/products", {
        query: { organization_id: selectedOrganizationId, limit: 200 }
      })
  });
  const locations = useQuery({
    queryKey: ["view-locations", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Location>>("/locations", {
        query: { organization_id: selectedOrganizationId, limit: 200 }
      })
  });
  const expiring = useInventoryView("expiring", selectedOrganizationId, {
    expires_from: todayIso,
    expires_to: soonIso
  });
  const expired = useInventoryView("expired", selectedOrganizationId, {
    expires_to: todayIso
  });
  const depleted = useInventoryView("depleted", selectedOrganizationId, {
    status: "depleted"
  });

  const queries = [products, locations, expiring, expired, depleted];
  if (queries.some((query) => query.isLoading)) return <LoadingState />;
  const failed = queries.find((query) => query.error);
  if (failed?.error) return <ErrorState error={failed.error} />;

  const productMap = new Map(products.data?.items.map((product) => [product.id, product.name]));
  const locationMap = new Map(locations.data?.items.map((location) => [location.id, location.name]));

  return (
    <div className="page">
      <div>
        <p className="eyebrow">Operational queues</p>
        <h2>Inventory views</h2>
      </div>
      <section>
        <h3>Expiring in the next 30 days</h3>
        <BatchTable
          batches={expiring.data?.items ?? []}
          productMap={productMap}
          locationMap={locationMap}
          canManageInventory={canManageInventory}
        />
      </section>
      <section>
        <h3>Expired</h3>
        <BatchTable
          batches={expired.data?.items ?? []}
          productMap={productMap}
          locationMap={locationMap}
          canManageInventory={canManageInventory}
        />
      </section>
      <section>
        <h3>Depleted</h3>
        <BatchTable
          batches={depleted.data?.items ?? []}
          productMap={productMap}
          locationMap={locationMap}
          canManageInventory={canManageInventory}
        />
      </section>
    </div>
  );
}

function useInventoryView(
  key: string,
  organizationId: string,
  query: Record<string, string>
) {
  return useQuery({
    queryKey: ["inventory-view", key, organizationId, query],
    enabled: Boolean(organizationId),
    queryFn: () =>
      apiClient.request<Page<Batch>>("/batches", {
        query: { organization_id: organizationId, limit: 100, ...query }
      })
  });
}
