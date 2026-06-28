import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { apiClient } from "../../api/client";
import { Batch, Location, Page, Product } from "../../api/generated/client";
import { useOrganization } from "../../shared/organization/OrganizationContext";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field, SelectField, TextAreaField } from "../../shared/ui/Field";
import { EmptyState, ErrorState, LoadingState } from "../../shared/ui/State";
import { BatchFormValues, batchSchema } from "./forms";
import { inventoryKeys } from "./queryKeys";

export function BatchesPage() {
  const queryClient = useQueryClient();
  const { selectedOrganizationId, canManageInventory } = useOrganization();
  const [status, setStatus] = useState("");
  const today = new Date().toISOString().slice(0, 10);
  const batches = useQuery({
    queryKey: inventoryKeys.batches(selectedOrganizationId, { status }),
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Batch>>("/batches", {
        query: { organization_id: selectedOrganizationId, status, limit: 50 }
      })
  });
  const products = useQuery({
    queryKey: inventoryKeys.products(selectedOrganizationId),
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Product>>("/products", {
        query: { organization_id: selectedOrganizationId, limit: 200 }
      })
  });
  const locations = useQuery({
    queryKey: inventoryKeys.locations(selectedOrganizationId),
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Location>>("/locations", {
        query: { organization_id: selectedOrganizationId, limit: 200, is_active: true }
      })
  });
  const form = useForm<BatchFormValues>({
    resolver: zodResolver(batchSchema),
    defaultValues: {
      product_id: "",
      location_id: "",
      batch_number: "",
      quantity_received: 0,
      quantity_available: 0,
      received_date: today,
      expiry_date: today,
      notes: ""
    }
  });
  const createBatch = useMutation({
    mutationFn: (values: BatchFormValues) =>
      apiClient.request<Batch>("/batches", {
        method: "POST",
        body: { ...values, organization_id: selectedOrganizationId }
      }),
    onSuccess: async () => {
      form.reset();
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard-expiring"] });
    }
  });
  const markDepleted = useMutation({
    mutationFn: (batch: Batch) =>
      apiClient.request<Batch>(`/batches/${batch.id}`, {
        method: "PATCH",
        body: { quantity_available: 0, status: "depleted" }
      }),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["batches"] })
  });

  const error = batches.error ?? products.error ?? locations.error ?? createBatch.error;
  if (batches.isLoading || products.isLoading || locations.isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  const productMap = new Map(products.data?.items.map((product) => [product.id, product.name]));
  const locationMap = new Map(locations.data?.items.map((location) => [location.id, location.name]));

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Inventory units</p>
          <h2>Batches</h2>
        </div>
        <label className="field compact">
          <span>Status</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="depleted">Depleted</option>
            <option value="quarantined">Quarantined</option>
          </select>
        </label>
      </header>

      {canManageInventory ? (
        <Card>
          <h3>Add batch</h3>
          <form
            className="form-grid"
            onSubmit={form.handleSubmit((values) => createBatch.mutate(values))}
          >
            <SelectField label="Product" {...form.register("product_id")} error={form.formState.errors.product_id?.message}>
              <option value="">Select product</option>
              {products.data?.items.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </SelectField>
            <SelectField label="Location" {...form.register("location_id")} error={form.formState.errors.location_id?.message}>
              <option value="">Select location</option>
              {locations.data?.items.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </SelectField>
            <Field label="Batch number" {...form.register("batch_number")} error={form.formState.errors.batch_number?.message} />
            <Field label="Received quantity" type="number" {...form.register("quantity_received")} />
            <Field label="Available quantity" type="number" {...form.register("quantity_available")} error={form.formState.errors.quantity_available?.message} />
            <Field label="Received date" type="date" {...form.register("received_date")} />
            <Field label="Expiry date" type="date" {...form.register("expiry_date")} />
            <TextAreaField label="Notes" {...form.register("notes")} />
            <Button type="submit" disabled={createBatch.isPending}>
              Create batch
            </Button>
          </form>
        </Card>
      ) : null}

      <BatchTable
        batches={batches.data?.items ?? []}
        productMap={productMap}
        locationMap={locationMap}
        canManageInventory={canManageInventory}
        onMarkDepleted={(batch) => markDepleted.mutate(batch)}
      />
    </div>
  );
}

export function BatchTable({
  batches,
  productMap,
  locationMap,
  canManageInventory,
  onMarkDepleted
}: {
  batches: Batch[];
  productMap: Map<string, string>;
  locationMap: Map<string, string>;
  canManageInventory: boolean;
  onMarkDepleted?: (batch: Batch) => void;
}) {
  return (
    <Card>
      {batches.length ? (
        <table>
          <thead>
            <tr>
              <th>Batch</th>
              <th>Product</th>
              <th>Location</th>
              <th>Available</th>
              <th>Expiry</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {batches.map((batch) => (
              <tr key={batch.id}>
                <td>{batch.batch_number}</td>
                <td>{productMap.get(batch.product_id) ?? batch.product_id}</td>
                <td>{locationMap.get(batch.location_id) ?? batch.location_id}</td>
                <td>
                  {batch.quantity_available}/{batch.quantity_received}
                </td>
                <td>{batch.expiry_date}</td>
                <td>{batch.status}</td>
                <td>
                  {canManageInventory && batch.status !== "depleted" ? (
                    <Button variant="secondary" onClick={() => onMarkDepleted?.(batch)}>
                      Mark depleted
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState message="No batches match this view." />
      )}
    </Card>
  );
}
