import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { Batch, Page, Product } from "../../api/generated/client";
import { useOrganization } from "../../shared/organization/OrganizationContext";
import { Card } from "../../shared/ui/Card";
import { ErrorState, LoadingState } from "../../shared/ui/State";

export function DashboardPage() {
  const { selectedOrganizationId } = useOrganization();
  const today = new Date();
  const inThirtyDays = new Date(today);
  inThirtyDays.setDate(today.getDate() + 30);

  const products = useQuery({
    queryKey: ["dashboard-products", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Product>>("/products", {
        query: { organization_id: selectedOrganizationId, limit: 1 }
      })
  });
  const expiring = useQuery({
    queryKey: ["dashboard-expiring", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Batch>>("/batches", {
        query: {
          organization_id: selectedOrganizationId,
          expires_from: today.toISOString().slice(0, 10),
          expires_to: inThirtyDays.toISOString().slice(0, 10),
          limit: 1
        }
      })
  });
  const expired = useQuery({
    queryKey: ["dashboard-expired", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Batch>>("/batches", {
        query: {
          organization_id: selectedOrganizationId,
          expires_to: today.toISOString().slice(0, 10),
          limit: 1
        }
      })
  });
  const depleted = useQuery({
    queryKey: ["dashboard-depleted", selectedOrganizationId],
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Batch>>("/batches", {
        query: { organization_id: selectedOrganizationId, status: "depleted", limit: 1 }
      })
  });

  const queries = [products, expiring, expired, depleted];
  if (queries.some((query) => query.isLoading)) {
    return <LoadingState />;
  }
  const failed = queries.find((query) => query.error);
  if (failed?.error) {
    return <ErrorState error={failed.error} />;
  }

  return (
    <div className="page">
      <div>
        <p className="eyebrow">Overview</p>
        <h2>Inventory dashboard</h2>
      </div>
      <div className="metric-grid">
        <Metric label="Products" value={products.data?.total ?? 0} />
        <Metric label="Expiring in 30 days" value={expiring.data?.total ?? 0} />
        <Metric label="Expired" value={expired.data?.total ?? 0} />
        <Metric label="Depleted" value={depleted.data?.total ?? 0} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <p>{label}</p>
      <strong className="metric">{value}</strong>
    </Card>
  );
}
