import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

import { apiClient } from "../../api/client";
import { Location, Page } from "../../api/generated/client";
import { useOrganization } from "../../shared/organization/OrganizationContext";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field, TextAreaField } from "../../shared/ui/Field";
import { EmptyState, ErrorState, LoadingState } from "../../shared/ui/State";
import { LocationFormValues, locationSchema } from "./forms";
import { inventoryKeys } from "./queryKeys";

export function LocationsPage() {
  const queryClient = useQueryClient();
  const { selectedOrganizationId, canManageInventory } = useOrganization();
  const query = useQuery({
    queryKey: inventoryKeys.locations(selectedOrganizationId),
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Location>>("/locations", {
        query: { organization_id: selectedOrganizationId, limit: 100 }
      })
  });
  const form = useForm<LocationFormValues>({
    resolver: zodResolver(locationSchema),
    defaultValues: { code: "", name: "", timezone: "UTC", address: "" }
  });
  const createLocation = useMutation({
    mutationFn: (values: LocationFormValues) =>
      apiClient.request<Location>("/locations", {
        method: "POST",
        body: { ...values, organization_id: selectedOrganizationId }
      }),
    onSuccess: async () => {
      form.reset({ code: "", name: "", timezone: "UTC", address: "" });
      await queryClient.invalidateQueries({ queryKey: ["locations"] });
    }
  });
  const toggleLocation = useMutation({
    mutationFn: (location: Location) =>
      apiClient.request<Location>(`/locations/${location.id}`, {
        method: "PATCH",
        body: { is_active: !location.is_active }
      }),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["locations"] })
  });

  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState error={query.error} />;

  return (
    <div className="page">
      <div>
        <p className="eyebrow">Storage</p>
        <h2>Locations</h2>
      </div>

      {canManageInventory ? (
        <Card>
          <h3>Add location</h3>
          <form
            className="form-grid"
            onSubmit={form.handleSubmit((values) => createLocation.mutate(values))}
          >
            <Field label="Code" {...form.register("code")} error={form.formState.errors.code?.message} />
            <Field label="Name" {...form.register("name")} error={form.formState.errors.name?.message} />
            <Field label="Timezone" {...form.register("timezone")} />
            <TextAreaField label="Address" {...form.register("address")} />
            <Button type="submit" disabled={createLocation.isPending}>
              Create location
            </Button>
          </form>
          {createLocation.error ? <ErrorState error={createLocation.error} /> : null}
        </Card>
      ) : null}

      <Card>
        {query.data?.items.length ? (
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Timezone</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((location) => (
                <tr key={location.id}>
                  <td>{location.code}</td>
                  <td>{location.name}</td>
                  <td>{location.timezone}</td>
                  <td>{location.is_active ? "active" : "inactive"}</td>
                  <td>
                    {canManageInventory ? (
                      <Button
                        variant="secondary"
                        onClick={() => toggleLocation.mutate(location)}
                      >
                        {location.is_active ? "Deactivate" : "Reactivate"}
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState message="No locations yet." />
        )}
      </Card>
    </div>
  );
}
