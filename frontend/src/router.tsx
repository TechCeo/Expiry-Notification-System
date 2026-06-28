import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "./shell/AppLayout";
import { AuthCallbackPage } from "./features/auth/AuthCallbackPage";
import { LoginPage } from "./features/auth/LoginPage";
import { BatchesPage } from "./features/inventory/BatchesPage";
import { DashboardPage } from "./features/inventory/DashboardPage";
import { InventoryViewsPage } from "./features/inventory/InventoryViewsPage";
import { LocationsPage } from "./features/inventory/LocationsPage";
import { ProductsPage } from "./features/inventory/ProductsPage";
import { OrganizationProvider } from "./shared/organization/OrganizationContext";
import { RequireAuth } from "./shared/auth/RequireAuth";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/auth/callback", element: <AuthCallbackPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: (
          <OrganizationProvider>
            <AppLayout />
          </OrganizationProvider>
        ),
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/products", element: <ProductsPage /> },
          { path: "/locations", element: <LocationsPage /> },
          { path: "/batches", element: <BatchesPage /> },
          { path: "/inventory-views", element: <InventoryViewsPage /> }
        ]
      }
    ]
  }
]);
