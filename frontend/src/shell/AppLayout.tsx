import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { apiClient } from "../api/client";
import { Organization } from "../api/generated/client";
import { useAuth } from "../shared/auth/AuthProvider";
import { useOrganization } from "../shared/organization/OrganizationContext";
import { Button } from "../shared/ui/Button";
import { Card } from "../shared/ui/Card";
import { Field } from "../shared/ui/Field";
import { ErrorState } from "../shared/ui/State";

const navItems = [
  ["Dashboard", "/dashboard"],
  ["Products", "/products"],
  ["Locations", "/locations"],
  ["Batches", "/batches"],
  ["Views", "/inventory-views"]
] as const;

export function AppLayout() {
  const auth = useAuth();
  const org = useOrganization();
  const hasOrganizations = org.organizations.length > 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Expiry Notification</p>
          <h1>Inventory OS</h1>
        </div>
        {hasOrganizations ? (
          <>
            <label className="field">
              <span>Organization</span>
              <select
                value={org.selectedOrganizationId}
                onChange={(event) => org.setSelectedOrganizationId(event.target.value)}
              >
                {org.organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </select>
            </label>
            <nav>
              {navItems.map(([label, href]) => (
                <NavLink key={href} to={href}>
                  {label}
                </NavLink>
              ))}
            </nav>
          </>
        ) : null}
        <div className="user-panel">
          <span>{org.me?.email ?? org.me?.display_name ?? "Signed in"}</span>
          <small>Role: {org.role ?? "none"}</small>
          <Button variant="secondary" onClick={() => void auth.logout()}>
            Log out
          </Button>
        </div>
      </aside>
      <main className="main-content">
        {hasOrganizations ? <Outlet /> : <CreateOrganizationPanel />}
      </main>
    </div>
  );
}

function CreateOrganizationPanel() {
  const queryClient = useQueryClient();
  const org = useOrganization();
  const [name, setName] = useState("My Inventory Organization");
  const [slug, setSlug] = useState("my-inventory-organization");
  const suggestedSlug = useMemo(() => toSlug(name), [name]);
  const createOrganization = useMutation({
    mutationFn: () =>
      apiClient.request<Organization>("/organizations", {
        method: "POST",
        body: { name: name.trim(), slug: slug.trim() || suggestedSlug }
      }),
    onSuccess: async (organization) => {
      org.setSelectedOrganizationId(organization.id);
      await queryClient.invalidateQueries({ queryKey: ["organizations"] });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    }
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    createOrganization.mutate();
  };

  return (
    <div className="auth-page">
      <Card>
        <p className="eyebrow">First-time setup</p>
        <h2>Create your organization</h2>
        <p>
          Your login worked. Create the first organization to become its owner
          and unlock inventory workflows.
        </p>
        <form className="stack" onSubmit={submit}>
          <Field
            label="Organization name"
            value={name}
            onChange={(event) => {
              const nextName = event.target.value;
              setName(nextName);
              setSlug(toSlug(nextName));
            }}
            required
            minLength={1}
            maxLength={120}
          />
          <Field
            label="URL-safe slug"
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            required
            minLength={2}
            maxLength={63}
            pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
          />
          <Button type="submit" disabled={createOrganization.isPending}>
            Create organization
          </Button>
        </form>
        {createOrganization.error ? (
          <ErrorState error={createOrganization.error} />
        ) : null}
      </Card>
    </div>
  );
}

function toSlug(value: string) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 63) || "inventory"
  );
}
