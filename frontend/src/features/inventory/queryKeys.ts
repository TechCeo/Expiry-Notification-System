export const inventoryKeys = {
  products: (organizationId: string, filters?: unknown) =>
    ["products", organizationId, filters] as const,
  locations: (organizationId: string, filters?: unknown) =>
    ["locations", organizationId, filters] as const,
  batches: (organizationId: string, filters?: unknown) =>
    ["batches", organizationId, filters] as const
};
