import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../shared/auth/AuthProvider";
import { useOrganization } from "../shared/organization/OrganizationContext";
import { Button } from "../shared/ui/Button";

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

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Expiry Notification</p>
          <h1>Inventory OS</h1>
        </div>
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
        <div className="user-panel">
          <span>{org.me?.user.email ?? org.me?.user.display_name ?? "Signed in"}</span>
          <small>Role: {org.role ?? "none"}</small>
          <Button variant="secondary" onClick={() => void auth.logout()}>
            Log out
          </Button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
