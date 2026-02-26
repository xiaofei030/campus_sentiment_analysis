import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import OverviewPage from './pages/OverviewPage'
import MonitoringPage from './pages/MonitoringPage'
import SentimentPage from './pages/SentimentPage'
import TopicsPage from './pages/TopicsPage'
import AlertsPage from './pages/AlertsPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import AnalysisPage from './pages/AnalysisPage'
import CollectorPage from './pages/CollectorPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/sentiment" element={<SentimentPage />} />
          <Route path="/topics" element={<TopicsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/collector" element={<CollectorPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
