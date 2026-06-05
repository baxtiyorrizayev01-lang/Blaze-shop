import React, { useState, useEffect } from 'react'
import useStore from '../store/useStore'

export default function AdminPage() {
  const { user } = useStore()
  const [tab, setTab] = useState('stats')
  const [stats, setStats] = useState(null)

  useEffect(() => {
    // Load admin stats
    fetch('/api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'admin_stats', telegram_id: user?.telegram_id })
    }).then(r => r.json()).then(d => d.stats && setStats(d.stats))
  }, [])

  return (
    <div className="page" style={{ padding: '16px' }}>
      <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 16 }}>🔧 Admin Panel</div>
      <div style={{ fontSize: 13, color: '#888', marginBottom: 20 }}>
        Keng admin panel brauzerda mavjud:
      </div>
      <a href="/admin" target="_blank" className="btn-primary" style={{ display: 'flex', textDecoration: 'none', justifyContent: 'center', marginBottom: 12 }}>
        🖥️ Admin Panelni Ochish
      </a>
    </div>
  )
}
