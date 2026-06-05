import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'
import SkinCard from '../components/SkinCard'

function BannerSlider() {
  const [idx, setIdx] = useState(0)
  const banners = [
    { title: 'CS2 Skinlar', sub: 'Eng yaxshi skinlar eng qulay narxlarda', color: '#FF6B00', icon: '🔥' },
    { title: 'Haftalik Giveaway', sub: 'AK-47 | Redline yutib oling!', color: '#9b59b6', icon: '🎁' },
    { title: 'Referal Bonus', sub: 'Do\'stingizni taklif qiling +5,000 so\'m', color: '#00d084', icon: '👥' },
  ]
  useEffect(() => {
    const t = setInterval(() => setIdx(i => (i + 1) % banners.length), 3500)
    return () => clearInterval(t)
  }, [])
  const b = banners[idx]
  return (
    <div style={{
      borderRadius: 20, padding: '20px 20px', marginBottom: 20,
      background: `linear-gradient(135deg, ${b.color}30, ${b.color}10)`,
      border: `1px solid ${b.color}40`, position: 'relative', overflow: 'hidden',
      transition: 'all .4s ease', minHeight: 110
    }}>
      <div style={{ position: 'absolute', right: -10, top: -10, fontSize: 80, opacity: .12 }}>{b.icon}</div>
      <div style={{ position: 'absolute', right: 20, top: '50%', transform: 'translateY(-50%)', fontSize: 56, opacity: .25 }}>{b.icon}</div>
      <div style={{ fontSize: 18, fontWeight: 800, color: '#fff', marginBottom: 6 }}>{b.title}</div>
      <div style={{ fontSize: 13, color: '#ccc', marginBottom: 14 }}>{b.sub}</div>
      <div style={{ display: 'flex', gap: 6 }}>
        {banners.map((_, i) => (
          <div key={i} onClick={() => setIdx(i)} style={{
            width: i === idx ? 20 : 6, height: 6, borderRadius: 3,
            background: i === idx ? b.color : 'rgba(255,255,255,0.2)',
            cursor: 'pointer', transition: 'all .3s'
          }}/>
        ))}
      </div>
    </div>
  )
}

function BalanceCard({ user, onDeposit }) {
  return (
    <div style={{
      borderRadius: 20, padding: 20, marginBottom: 20,
      background: 'linear-gradient(135deg, rgba(255,107,0,0.15), rgba(255,107,0,0.05))',
      border: '1px solid rgba(255,107,0,0.3)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 11, color: '#888', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.05em' }}>Balansingiz</div>
          <div style={{ fontSize: 28, fontWeight: 900, color: '#FF6B00', lineHeight: 1 }}>
            {(user?.balance || 0).toLocaleString()} <span style={{ fontSize: 16, fontWeight: 600 }}>so'm</span>
          </div>
        </div>
        <div style={{
          width: 52, height: 52, borderRadius: 16,
          background: 'linear-gradient(135deg,#FF6B00,#ff3300)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 24, boxShadow: '0 4px 20px rgba(255,107,0,0.4)'
        }}>🔥</div>
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn-primary" style={{ flex: 1, padding: '11px' }} onClick={onDeposit}>
          + To'ldirish
        </button>
        <button className="btn-ghost" style={{ flex: 1, padding: '11px', fontSize: 13 }}>
          📋 Tarix
        </button>
      </div>
    </div>
  )
}

function QuickActions({ setPage }) {
  const actions = [
    { icon: '🛒', label: 'Shop', page: 'shop', color: '#FF6B00' },
    { icon: '🎁', label: 'Giveaway', page: 'giveaway', color: '#9b59b6' },
    { icon: '👥', label: 'Referal', page: 'profile', color: '#00d084' },
    { icon: '📦', label: 'Buyurtmalar', page: 'profile', color: '#3498db' },
  ]
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginBottom: 22 }}>
      {actions.map(a => (
        <div key={a.label} onClick={() => setPage(a.page)} style={{
          background: `${a.color}12`, border: `1px solid ${a.color}25`,
          borderRadius: 14, padding: '14px 8px', textAlign: 'center', cursor: 'pointer',
          transition: 'all .15s'
        }}>
          <div style={{ fontSize: 24, marginBottom: 6 }}>{a.icon}</div>
          <div style={{ fontSize: 10, fontWeight: 600, color: '#ccc' }}>{a.label}</div>
        </div>
      ))}
    </div>
  )
}

export default function HomePage() {
  const { user, featuredSkins, giveaways, loadSkins, setPage } = useStore()
  const [popularSkins, setPopularSkins] = useState([])

  useEffect(() => {
    loadSkins({ sort: 'price_desc', limit: 8 }).then(() => {
      useStore.getState().skins && setPopularSkins(useStore.getState().skins.slice(0, 8))
    })
  }, [])

  useEffect(() => {
    setPopularSkins(useStore.getState().skins.slice(0, 8))
  }, [useStore.getState().skins.length])

  return (
    <div className="page" style={{ padding: '16px 16px 0' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 11, color: '#888', fontWeight: 600 }}>Xush kelibsiz,</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#fff' }}>
            {user?.first_name || 'Do\'st'} 👋
          </div>
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: 14,
          background: 'linear-gradient(135deg,#FF6B00,#ff3300)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, fontWeight: 800, boxShadow: '0 4px 15px rgba(255,107,0,0.4)',
          fontFamily: "'Barlow Condensed',sans-serif"
        }}>B</div>
      </div>

      <BannerSlider />
      <BalanceCard user={user} onDeposit={() => setPage('balance')} />
      <QuickActions setPage={setPage} />

      {/* Featured */}
      {featuredSkins.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="section-title">🔥 Featured Skinlar</div>
            <button onClick={() => setPage('shop')} style={{ fontSize: 12, color: '#FF6B00', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Hammasi →</button>
          </div>
          <div className="scroll-x">
            {featuredSkins.map(s => (
              <SkinCard key={s.id} skin={s} compact onClick={() => {
                useStore.getState().setPage('shop')
                setTimeout(() => useStore.setState({ selectedSkin: s }), 100)
              }}/>
            ))}
          </div>
        </div>
      )}

      {/* Active Giveaways */}
      {giveaways.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="section-title">🎁 Faol Giveawaylar</div>
            <button onClick={() => setPage('giveaway')} style={{ fontSize: 12, color: '#FF6B00', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Hammasi →</button>
          </div>
          {giveaways.slice(0, 2).map(g => (
            <GiveawayMiniCard key={g.id} g={g} onClick={() => setPage('giveaway')} />
          ))}
        </div>
      )}

      {/* Popular skins */}
      <div style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="section-title">💎 Mashhur Skinlar</div>
          <button onClick={() => setPage('shop')} style={{ fontSize: 12, color: '#FF6B00', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Hammasi →</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {useStore.getState().skins.slice(0, 4).map(s => (
            <MiniSkinRow key={s.id} skin={s} onClick={() => setPage('shop')} />
          ))}
        </div>
      </div>
    </div>
  )
}

function GiveawayMiniCard({ g, onClick }) {
  const [timeLeft, setTimeLeft] = useState('')
  useEffect(() => {
    const update = () => {
      const diff = new Date(g.end_time) - new Date()
      if (diff <= 0) { setTimeLeft('Tugadi'); return }
      const d = Math.floor(diff / 86400000)
      const h = Math.floor((diff % 86400000) / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      setTimeLeft(d > 0 ? `${d}k ${h}s` : `${h}s ${m}m`)
    }
    update(); const t = setInterval(update, 60000); return () => clearInterval(t)
  }, [g.end_time])
  const pct = Math.min(100, Math.round((g.participant_count / g.max_participants) * 100))
  return (
    <div onClick={onClick} style={{
      background: 'rgba(155,89,182,0.1)', border: '1px solid rgba(155,89,182,0.25)',
      borderRadius: 16, padding: 14, marginBottom: 10, cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'center'
    }}>
      <div style={{ fontSize: 32, flexShrink: 0 }}>🎁</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 3 }}>{g.title}</div>
        <div style={{ fontSize: 11, color: '#9b59b6', marginBottom: 8 }}>🏆 {g.prize_name}</div>
        <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, height: 4, marginBottom: 4 }}>
          <div style={{ width: `${pct}%`, height: '100%', background: '#9b59b6', borderRadius: 4, transition: 'width .4s' }}/>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#888' }}>
          <span>👥 {g.participant_count}/{g.max_participants}</span>
          <span>⏰ {timeLeft}</span>
        </div>
      </div>
    </div>
  )
}

function MiniSkinRow({ skin, onClick }) {
  const colors = { Rifle: '#c0392b', 'Sniper Rifle': '#8e44ad', Pistol: '#f39c12', Knife: '#f1c40f' }
  const c = colors[skin.weapon_type] || '#FF6B00'
  return (
    <div onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 12,
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, padding: '11px 14px', cursor: 'pointer'
    }}>
      <div style={{ width: 50, height: 32, borderRadius: 8, background: `${c}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 20 }}>
        {skin.weapon_type === 'Knife' ? '🗡️' : skin.weapon_type === 'Pistol' ? '🔫' : '⚔️'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{skin.name}</div>
        <div style={{ fontSize: 11, color: '#888' }}>{skin.exterior}</div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: 13, color: '#FF6B00', fontWeight: 800 }}>{(skin.price/1000).toFixed(0)}K</div>
        <div style={{ fontSize: 10, color: '#888' }}>so'm</div>
      </div>
    </div>
  )
}
