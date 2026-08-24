// SatInsight AI — Satellite Data Page

import Layout from '../components/layout/Layout'
import TelemetryTable from '../components/tables/TelemetryTable'
import FileUpload from '../components/ui/FileUpload'
import { useStore } from '../store/dataStore'

export default function SatelliteData() {
  const { sessionId, datasetName, rowCount, loadSample, isLoading } = useStore()

  return (
    <Layout
      title="Satellite Data"
      subtitle={sessionId ? `${datasetName} · ${rowCount.toLocaleString()} rows` : 'No dataset loaded'}
    >
      {!sessionId ? (
        <div style={{ maxWidth: 560 }}>
          <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>
            Load a dataset to explore raw telemetry records.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button
              onClick={loadSample}
              disabled={isLoading}
              style={{
                padding: '9px 20px', borderRadius: 8, fontSize: 13,
                background: '#1d4ed8', border: 'none', color: '#fff', cursor: 'pointer', width: 'fit-content',
              }}
            >
              Load Sample Dataset
            </button>
            <FileUpload />
          </div>
        </div>
      ) : (
        <TelemetryTable />
      )}
    </Layout>
  )
}
