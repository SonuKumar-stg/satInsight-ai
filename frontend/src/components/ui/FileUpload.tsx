// SatInsight AI — Drag-and-drop CSV File Upload

import { useCallback, useState } from 'react'
import { useStore } from '../../store/dataStore'

export default function FileUpload() {
  const { uploadFile, isLoading } = useStore()
  const [dragging, setDragging] = useState(false)

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith('.csv')) return
      uploadFile(file)
    },
    [uploadFile]
  )

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''   // allow re-upload of same file
  }

  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        padding: '28px 24px',
        borderRadius: 10,
        border: `2px dashed ${dragging ? '#3b82f6' : '#1e3a5f'}`,
        background: dragging ? 'rgba(59,130,246,0.06)' : '#0a1628',
        cursor: isLoading ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s',
        textAlign: 'center',
      }}
    >
      <span style={{ fontSize: 28, opacity: 0.6 }}>📂</span>
      <div>
        <div style={{ color: '#94a3b8', fontSize: 13 }}>
          Drop a CSV file here, or <span style={{ color: '#3b82f6' }}>browse</span>
        </div>
        <div style={{ color: '#475569', fontSize: 11, marginTop: 4 }}>
          Required columns: timestamp, temperature, radiation, pressure,<br/>
          battery_level, signal_strength, velocity, altitude
        </div>
      </div>
      <input
        type="file"
        accept=".csv"
        onChange={onInputChange}
        disabled={isLoading}
        style={{ display: 'none' }}
      />
    </label>
  )
}
