export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type OrganizationRole = "viewer" | "inventory_manager" | "admin" | "owner";
export type ProductStatus = "active" | "archived";
export type BatchStatus = "active" | "depleted" | "quarantined" | "expired";

export type Organization = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type Product = {
  id: string;
  organization_id: string;
  sku: string;
  name: string;
  description: string | null;
  category: string | null;
  status: ProductStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Location = {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  timezone: string;
  address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Batch = {
  id: string;
  organization_id: string;
  product_id: string;
  location_id: string;
  batch_number: string;
  quantity_received: number;
  quantity_available: number;
  expiry_date: string;
  received_date: string;
  status: BatchStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  oidc_subject: string;
  email: string | null;
  email_verified: boolean;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Membership = {
  id: string;
  organization_id: string;
  user_id: string;
  role: OrganizationRole;
  created_at: string;
  updated_at: string;
  user?: User;
};

export type Me = {
  user: User;
  memberships: Membership[];
};

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details: unknown
  ) {
    super(message);
  }
}

export class ExpiryApiClient {
  constructor(
    private readonly baseUrl: string,
    private readonly getAccessToken: () => Promise<string | null>
  ) {}

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const token = await this.getAccessToken();
    const url = new URL(`${this.baseUrl}${path}`);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
    const response = await fetch(url, {
      method: options.method ?? "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: options.body ? JSON.stringify(options.body) : undefined
    });
    if (response.status === 204) {
      return undefined as T;
    }
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        payload?.detail ?? payload?.message ?? "API request failed",
        response.status,
        payload
      );
    }
    return payload as T;
  }
}
