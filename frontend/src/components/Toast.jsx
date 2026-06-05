import React from 'react'
export default function Toast({ message, type }) {
  const colors = { success: '#00d084', error: '#e74c3c', info: '#3498db', warning: '#f39c12' }
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' }
  return (
    <div style={{
      position: 'fixed', top: 20, left: 16, right: 16, zIndex: 9999,
      background: 'rgba(20,25,35,0.97)', border: `1px solid ${colors[type] || colors.info}40`,
      borderLeft: `4px solid ${colors[type] || colors.info}`,
      borderRadius: 14, padding: '14px 16px',
      display: 'flex', alignItems: 'center', gap: 10,
      backdropFilter: 'blur(20px)', animation: 'fadeUp .2s ease',
      boxShadow: `0 8px 30px rgba(0,0,0,0.5)`
    }}>
      <span style={{ fontSize: 18 }}>{icons[type] || icons.info}</span>
      <span style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{message}</span>
    </div>
  )
}
