import { Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import GroupsPage from './pages/GroupsPage'
import PromptsPage from './pages/PromptsPage'
import AnalysisPage from './pages/AnalysisPage'
import EvaluationsPage from './pages/EvaluationsPage'
import APIKeysPage from './pages/APIKeysPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <AnimatePresence mode="wait">
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="groups" element={<GroupsPage />} />
          <Route path="prompts" element={<PromptsPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="evaluations" element={<EvaluationsPage />} />
          <Route path="api-keys" element={<APIKeysPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </AnimatePresence>
  )
}

export default App

