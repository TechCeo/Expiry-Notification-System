import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useForm } from "react-hook-form";

import { apiClient } from "../../api/client";
import { Page, Product } from "../../api/generated/client";
import { useOrganization } from "../../shared/organization/OrganizationContext";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field, TextAreaField } from "../../shared/ui/Field";
import { EmptyState, ErrorState, LoadingState } from "../../shared/ui/State";
import { ProductFormValues, productSchema } from "./forms";
import { inventoryKeys } from "./queryKeys";

export function ProductsPage() {
  const queryClient = useQueryClient();
  const { selectedOrganizationId, canManageInventory } = useOrganization();
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const filters = { search, offset };
  const query = useQuery({
    queryKey: inventoryKeys.products(selectedOrganizationId, filters),
    enabled: Boolean(selectedOrganizationId),
    queryFn: () =>
      apiClient.request<Page<Product>>("/products", {
        query: {
          organization_id: selectedOrganizationId,
          search,
          limit: 20,
          offset
        }
      })
  });
  const form = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: { sku: "", name: "", category: "", description: "" }
  });
  const createProduct = useMutation({
    mutationFn: (values: ProductFormValues) =>
      apiClient.request<Product>("/products", {
        method: "POST",
        body: { ...values, organization_id: selectedOrganizationId, metadata: {} }
      }),
    onSuccess: async () => {
      form.reset();
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard-products"] });
    }
  });
  const archiveProduct = useMutation({
    mutationFn: (product: Product) =>
      apiClient.request<Product>(`/products/${product.id}`, {
        method: "PATCH",
        body: { status: product.status === "active" ? "archived" : "active" }
      }),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["products"] })
  });

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    setOffset(0);
  };

  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState error={query.error} />;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Catalog</p>
          <h2>Products</h2>
        </div>
        <form onSubmit={submitSearch} className="inline-form">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search SKU or name"
            aria-label="Search products"
          />
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
      </header>

      {canManageInventory ? (
        <Card>
          <h3>Add product</h3>
          <form
            className="form-grid"
            onSubmit={form.handleSubmit((values) => createProduct.mutate(values))}
          >
            <Field label="SKU" {...form.register("sku")} error={form.formState.errors.sku?.message} />
            <Field label="Name" {...form.register("name")} error={form.formState.errors.name?.message} />
            <Field label="Category" {...form.register("category")} />
            <TextAreaField label="Description" {...form.register("description")} />
            <Button type="submit" disabled={createProduct.isPending}>
              Create product
            </Button>
          </form>
          {createProduct.error ? <ErrorState error={createProduct.error} /> : null}
        </Card>
      ) : null}

      <Card>
        {query.data?.items.length ? (
          <>
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((product) => (
                  <tr key={product.id}>
                    <td>{product.sku}</td>
                    <td>{product.name}</td>
                    <td>{product.category ?? "—"}</td>
                    <td>{product.status}</td>
                    <td>
                      {canManageInventory ? (
                        <Button
                          variant="secondary"
                          onClick={() => archiveProduct.mutate(product)}
                        >
                          {product.status === "active" ? "Archive" : "Restore"}
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination
              total={query.data.total}
              offset={offset}
              setOffset={setOffset}
            />
          </>
        ) : (
          <EmptyState message="No products yet." />
        )}
      </Card>
    </div>
  );
}

function Pagination({
  total,
  offset,
  setOffset
}: {
  total: number;
  offset: number;
  setOffset: (offset: number) => void;
}) {
  return (
    <div className="pagination">
      <Button
        variant="secondary"
        disabled={offset === 0}
        onClick={() => setOffset(Math.max(0, offset - 20))}
      >
        Previous
      </Button>
      <span>
        {offset + 1}-{Math.min(offset + 20, total)} of {total}
      </span>
      <Button
        variant="secondary"
        disabled={offset + 20 >= total}
        onClick={() => setOffset(offset + 20)}
      >
        Next
      </Button>
    </div>
  );
}
