// PLEASE WALANG GAGALAW NG KAHIT ANO
import { Navigate, Route, Routes } from 'react-router-dom'
import { AdminLayout } from './components/layout/AdminLayout'
import { LoginRoute } from './components/login/LoginRoute'
import { DashboardPage } from './pages/DashboardPage'
import { NetworkHealthPage } from './pages/NetworkHealthPage'
import { DeviceInventoryPage } from './pages/DeviceInventoryPage'
import { TopologyPage } from './pages/wagpakielaman'
import { SystemStatusPage } from './pages/SystemStatusPage'
import { ReportsPage } from './pages/ReportsPage'
import { HistoryPage } from './pages/HistoryPage'
import { SystemLogsPage } from './pages/SystemLogsPage'
import { ManageAccountsPage } from './pages/ManageAccountsPage'
import { PluginsPage } from './pages/PluginsPage'
import { NcpaDeploymentPage } from './pages/NcpaDeploymentPage'
import { RemediationPage } from './pages/RemediationPage'
import { SettingsPage } from './pages/SettingsPage'
import { ManageRolesPage } from './pages/ManageRolesPage'
import { MaintenancePage } from './pages/MaintenancePage'

export default function App() {
  return (
    <Routes>
      
      <Route
        path="/login"
        element={<LoginRoute />}
      />
      <Route
        path="/"
        element={<AdminLayout />}
      >
        <Route
          index
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />
        <Route
          path="dashboard"
          element={<DashboardPage />}
        />
        <Route
          path="network-health"
          element={<NetworkHealthPage />}
        />
        <Route
          path="device-inventory"
          element={<DeviceInventoryPage />}
        />

        <Route path="system-status" element={<SystemStatusPage />} />
        <Route path="topology" element={<TopologyPage />} />
        

        <Route
          path="history"
          element={<HistoryPage />}
        />
        <Route
          path="reports"
          element={<ReportsPage />}
        />
        <Route
          path="system-logs"
          element={<SystemLogsPage />}
        />
        <Route
          path="accounts"
          element={<ManageAccountsPage />}
        />
        <Route
          path="manage-roles"
          element={<ManageRolesPage />}
        />
        
        <Route
          path="plugins"
          element={<PluginsPage />}
        />
        <Route
          path="ncpa-deployment"
          element={<NcpaDeploymentPage />}
        />
        <Route
          path="maintenance"
          element={<MaintenancePage />}
        />
        <Route
          path="remediation"
          element={<RemediationPage />}
        />
        <Route
          path="settings"
          element={<SettingsPage />}
        />
      </Route>
      {/* Unknown routes */}
      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
    </Routes>
  )
}
