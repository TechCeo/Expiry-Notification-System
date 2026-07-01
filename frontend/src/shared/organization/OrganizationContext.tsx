import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { Me, Organization } from "../../api/generated/client";

type OrganizationContextValue = {
  me?: Me;
  organizations: Organization[];
  selectedOrganization?: Organization;
  selectedOrganizationId: string;
  setSelectedOrganizationId: (id: string) => void;
  role?: string;
  canManageInventory: boolean;
  canAdmin: boolean;
};

const OrganizationContext = createContext<OrganizationContextValue | null>(null);
const roleRank = { viewer: 1, inventory_manager: 2, admin: 3, owner: 4 };

export function OrganizationProvider({ children }: PropsWithChildren) {
  const [selectedOrganizationId, setSelectedOrganizationId] = useState(
    () => window.localStorage.getItem("expiry.organizationId") ?? ""
  );
  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.request<Me>("/me")
  });
  const organizationsQuery = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiClient.request<{ items: Organization[] }>("/organizations", {
      query: { limit: 100, offset: 0 }
    })
  });

  const organizations = useMemo(
    () => organizationsQuery.data?.items ?? [],
    [organizationsQuery.data?.items]
  );
  const resolvedOrganizationId = selectedOrganizationId || organizations[0]?.id || "";

  useEffect(() => {
    if (resolvedOrganizationId && resolvedOrganizationId !== selectedOrganizationId) {
      window.localStorage.setItem("expiry.organizationId", resolvedOrganizationId);
      setSelectedOrganizationId(resolvedOrganizationId);
    }
  }, [resolvedOrganizationId, selectedOrganizationId]);

  const selectedOrganization = organizations.find(
    (organization) => organization.id === resolvedOrganizationId
  );
  const membership = meQuery.data?.memberships.find(
    (item) => item.organization_id === resolvedOrganizationId
  );
  const rank = membership ? roleRank[membership.role] : 0;

  const value = useMemo<OrganizationContextValue>(
    () => ({
      me: meQuery.data,
      organizations,
      selectedOrganization,
      selectedOrganizationId: resolvedOrganizationId,
      setSelectedOrganizationId: (id: string) => {
        window.localStorage.setItem("expiry.organizationId", id);
        setSelectedOrganizationId(id);
      },
      role: membership?.role,
      canManageInventory: rank >= roleRank.inventory_manager,
      canAdmin: rank >= roleRank.admin
    }),
    [meQuery.data, organizations, selectedOrganization, resolvedOrganizationId, membership, rank]
  );

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganization must be used within OrganizationProvider");
  }
  return context;
}
