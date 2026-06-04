import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import ReconciliationWorkbench from './components/ReconciliationWorkbench'
import DisputeWorkbench from './components/DisputeWorkbench'
import QueryInterface from './components/QueryInterface'
import AuditTrail from './components/AuditTrail'
import PolicyManager from './components/PolicyManager'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reconciliation" element={<ReconciliationWorkbench />} />
          <Route path="/disputes" element={<DisputeWorkbench />} />
          <Route path="/query" element={<QueryInterface />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="/policy" element={<PolicyManager />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
