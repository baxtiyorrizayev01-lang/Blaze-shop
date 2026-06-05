import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'

function Countdown({ endTime }) {
  const [t, setT] = useState('')
  useEffect(() => {
    const upd = () => {
      const diff = new Date(endTime) - new Date()
      if (diff <= 0) { setT('Tugadi'); return }
      const d = Math.floor(diff / 86400000)
      const h = Math.floor((diff % 86400000) / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      setT(d > 0 ? `${d}k ${h}s ${m}m` : `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`)
    }
    upd(); const ti = setInterval(upd, 1000); return () => clearInterval(ti)
  }, [endTime])
  return <span style={{ fontFamily: 'monospace', fontSize: 16, fontWeight: 800, color: '#FF6B00' }}>{t}</span>
}

function GiveawayCard({ g, onJoin, joined, joining }) {
  const pct = Math.min(100, Math.round((g.participant_count / g.max_participants) * 100))
  const isFull = g.participant_count >= g.max_participants
  return (
    <div style={{
      background: 'rgba(155,89,182,0.08)', border: '1px solid rgba(155,89,182,0.2)',
      borderRadius: 20, overflow: 'hidden', marginBottom: 14
    }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(155,89,182,0.3),rgba(155,89,182,0.1))', padding: '16px 16px 12px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: -10, top: -10, fontSize: 70, opacity: .1 }}>🎁</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <div>
            <div style={{ fontSize: 11, color: '#9b59b6', fontWeight: 700, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.06em' }}>Giveaway #{g.id}</div>
            <div style={{ fontSize: 17, fontWeight: 800, color: '#fff', lineHeight: 1.2 }}>{g.title}</div>
          </div>
          <span className={`badge-${g.status}`}>{g.status === 'active' ? 'Faol' : 'Tugadi'}</span>
        </div>
        <div style={{ fontSize: 13, color: '#ccc', marginBottom: 8 }}>🏆 {g.prize_name}</div>
        {g.description && <div style={{ fontSize: 12, color: '#888', lineHeight: 1.5 }}>{g.description}</div>}
      </div>

      {/* Stats */}
      <div style={{ padding: '14px 16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
          <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>ISHTIROKCHILAR</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#9b59b6' }}>{g.participant_count}<span style={{ fontSize: 11, color: '#888' }}>/{g.max_participants}</span></div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>QOLGAN VAQT</div>
            <Countdown endTime={g.end_time}/>
          </div>
        </div>

        {/* Progress */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#888', marginBottom: 6 }}>
            <span>To'ldi: {pct}%</span>
            <span>{g.max_participants - g.participant_count} joy qoldi</span>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 6, height: 6 }}>
            <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#9b59b6,#8e44ad)', borderRadius: 6, transition: 'width .5s' }}/>
          </div>
        </div>

        {/* Requirements */}
        {g.min_balance > 0 && (
          <div style={{ background: 'rgba(243,156,18,0.1)', border: '1px solid rgba(243,156,18,0.2)', borderRadius: 10, padding: '8px 12px', marginBottom: 12, fontSize: 12, color: '#f39c12' }}>
            ⚠️ Minimal balans: {g.min_balance.toLocaleString()} so'm
          </div>
        )}

        {/* Join button */}
        {g.status === 'active' && (
          joined ? (
            <div style={{ background: 'rgba(0,208,132,0.1)', border: '1px solid rgba(0,208,132,0.3)', borderRadius: 14, padding: '13px', textAlign: 'center', fontSize: 14, fontWeight: 700, color: '#00d084' }}>
              ✅ Siz qatnashyapsiz!
            </div>
          ) : (
            <button className="btn-primary" onClick={() => onJoin(g.id)}
              disabled={joining || isFull}
              style={{
                background: isFull ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg,#9b59b6,#8e44ad)',
                boxShadow: isFull ? 'none' : '0 4px 20px rgba(155,89,182,0.35)',
                opacity: isFull ? 0.6 : 1
              }}>
              {joining ? '⏳ Yuklanmoqda...' : isFull ? '❌ Joylar tugadi' : '🎲 Qatnashish'}
            </button>
          )
        )}

        {g.status === 'ended' && g.winner_id && (
          <div style={{ background: 'rgba(241,196,15,0.1)', border: '1px solid rgba(241,196,15,0.3)', borderRadius: 12, padding: '10px 14px', fontSize: 13, color: '#f1c40f', textAlign: 'center' }}>
            🏆 G'olib tanlandi!
          </div>
        )}
      </div>
    </div>
  )
}

export default function GiveawayPage() {
  const { giveaways, loadGiveaways, joinGiveaway, loading } = useStore()
  const [tab, setTab] = useState('active')
  const [joinedIds, setJoinedIds] = useState(new Set())
  const [joiningId, setJoiningId] = useState(null)

  useEffect(() => {
    loadGiveaways()
  }, [])

  const handleJoin = async (gid) => {
    setJoiningId(gid)
    const res = await joinGiveaway(gid)
    if (!res?.error) setJoinedIds(prev => new Set([...prev, gid]))
    setJoiningId(null)
  }

  const filtered = tab === 'active'
    ? giveaways.filter(g => g.status === 'active')
    : giveaways.filter(g => g.status === 'ended')

  return (
    <div className="page" style={{ padding: '16px 16px 0' }}>
      <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 16 }}>🎁 Giveawaylar</div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 18, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 4 }}>
        {[{ val: 'active', label: '🟢 Faol' }, { val: 'ended', label: '⚫ Tugagan' }].map(t => (
          <button key={t.val} onClick={() => setTab(t.val)} style={{
            flex: 1, padding: '10px', borderRadius: 10, fontSize: 13, fontWeight: 600,
            cursor: 'pointer', border: 'none', transition: 'all .2s',
            background: tab === t.val ? 'linear-gradient(135deg,#FF6B00,#FF8C00)' : 'transparent',
            color: tab === t.val ? '#fff' : '#888'
          }}>{t.label}</button>
        ))}
      </div>

      {/* How it works */}
      {tab === 'active' && (
        <div style={{ background: 'rgba(52,152,219,0.08)', border: '1px solid rgba(52,152,219,0.2)', borderRadius: 16, padding: '14px 16px', marginBottom: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#3498db', marginBottom: 10 }}>ℹ️ Qanday ishlaydi?</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {['Giveawayni oching va "Qatnashish" tugmasini bosing', 'Vaqt tugaganda g\'olib tasodifiy tanlanadi', 'G\'olib Telegram orqali xabardor qilinadi'].map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, fontSize: 12, color: '#ccc' }}>
                <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#3498db', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 800, flexShrink: 0 }}>{i+1}</div>
                <span style={{ lineHeight: 1.5 }}>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Giveaways */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#666' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>{tab === 'active' ? '🎁' : '📋'}</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{tab === 'active' ? 'Faol giveaway yo\'q' : 'Tugagan giveaway yo\'q'}</div>
        </div>
      ) : (
        filtered.map(g => (
          <GiveawayCard key={g.id} g={g}
            onJoin={handleJoin}
            joined={joinedIds.has(g.id)}
            joining={joiningId === g.id}/>
        ))
      )}
    </div>
  )
}
