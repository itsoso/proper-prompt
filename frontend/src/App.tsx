import { Routes, Route } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Layout from './components/Layout'
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
        <Route path="/" element={<Layout />}>
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

