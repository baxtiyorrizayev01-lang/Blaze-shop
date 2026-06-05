import React from 'react'

const SKIN_COLORS = {
  Rifle: '#c0392b', 'Sniper Rifle': '#8e44ad',
  Pistol: '#f39c12', Knife: '#f1c40f', default: '#FF6B00'
}

function SkinSVG({ color, w = 140, h = 80 }) {
  const c = color || '#FF6B00'
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id={`g${c.replace('#','')}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={c} stopOpacity=".25"/>
          <stop offset="100%" stopColor={c} stopOpacity=".05"/>
        </linearGradient>
        <filter id="glow2"><feGaussianBlur stdDeviation="2" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width={w} height={h} fill={`url(#g${c.replace('#','')})`} rx="8"/>
      <rect x={w*.1} y={h*.38} width={w*.62} height={h*.17} rx="3" fill={c} opacity=".65" filter="url(#glow2)"/>
      <rect x={w*.58} y={h*.24} width={w*.14} height={h*.37} rx="2" fill={c} opacity=".5"/>
      <line x1={w*.72} y1={h*.44} x2={w*.93} y2={h*.44} stroke={c} strokeWidth="4" opacity=".8" filter="url(#glow2)"/>
      <rect x={w*.18} y={h*.44} width={w*.11} height={h*.24} rx="2" fill={c} opacity=".4"/>
      <rect x={w*.14} y={h*.38} width={w*.28} height="2" rx="1" fill="white" opacity=".15"/>
    </svg>
  )
}

export { SkinSVG, SKIN_COLORS }

export default function SkinCard({ skin, onClick, compact = false }) {
  const color = SKIN_COLORS[skin.weapon_type] || SKIN_COLORS.default
  if (compact) return (
    <div className="skin-card" style={{ width: 150, flexShrink: 0 }} onClick={onClick}>
      <div style={{ background: `${color}12`, padding: 12, display: 'flex', justifyContent: 'center' }}>
        <SkinSVG color={color} w={126} h={72}/>
      </div>
      <div style={{ padding: '10px 12px' }}>
        {skin.is_featured && <div style={{ fontSize: 9, color: '#FF6B00', fontWeight: 700, marginBottom: 4, letterSpacing: '.05em' }}>★ FEATURED</div>}
        <div style={{ fontSize: 12, fontWeight: 700, color: '#fff', lineHeight: 1.3, marginBottom: 4 }}>{skin.name}</div>
        <div style={{ fontSize: 10, color: '#888', marginBottom: 6 }}>{skin.exterior}</div>
        <div style={{ fontSize: 13, color: '#FF6B00', fontWeight: 800 }}>{skin.price.toLocaleString()} so'm</div>
      </div>
    </div>
  )
  return (
    <div className="skin-card" onClick={onClick}>
      <div style={{ background: `${color}12`, padding: 16, display: 'flex', justifyContent: 'center', position: 'relative' }}>
        {skin.is_featured && (
          <div style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(255,107,0,0.9)', borderRadius: 6, padding: '2px 7px', fontSize: 9, fontWeight: 800, letterSpacing: '.05em' }}>FEATURED</div>
        )}
        {skin.stock <= 2 && (
          <div style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(231,76,60,0.9)', borderRadius: 6, padding: '2px 7px', fontSize: 9, fontWeight: 800 }}>SON 1</div>
        )}
        <SkinSVG color={color} w={180} h={100}/>
      </div>
      <div style={{ padding: '12px 14px' }}>
        <div style={{ fontSize: 8, color: '#888', marginBottom: 3, letterSpacing: '.08em', textTransform: 'uppercase' }}>{skin.weapon_type}</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', lineHeight: 1.3, marginBottom: 4 }}>{skin.name}</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: 10, color: '#3498db', fontWeight: 600 }}>{skin.exterior}</span>
            {skin.float_val && <span style={{ fontSize: 10, color: '#666', marginLeft: 8 }}>Float: {skin.float_val}</span>}
          </div>
          <div style={{ fontSize: 14, color: '#FF6B00', fontWeight: 800 }}>{skin.price.toLocaleString()} so'm</div>
        </div>
      </div>
    </div>
  )
}
