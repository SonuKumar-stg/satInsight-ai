// SatInsight AI — Root Application Component

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Overview        from './pages/Overview'
import SatelliteData   from './pages/SatelliteData'
import DataAnalysis    from './pages/DataAnalysis'
import AnomalyDetection from './pages/AnomalyDetection'
import AIInsights      from './pages/AIInsights'
import Reports         from './pages/Reports'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<Overview />} />
        <Route path="/data"       element={<SatelliteData />} />
        <Route path="/analysis"   element={<DataAnalysis />} />
        <Route path="/anomalies"  element={<AnomalyDetection />} />
        <Route path="/insights"   element={<AIInsights />} />
        <Route path="/reports"    element={<Reports />} />
      </Routes>
    </BrowserRouter>
  )
}
