import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'

const METHODS = [
  { id: 'uzcard', label: 'UzCard', color: '#1e5bb5', icon: '🏦', number: '8600 4904 1234 5678' },
  { id: 'humo', label: 'Humo', color: '#f39c12', icon: '💳', number: '9860 1201 1234 5678' },
  { id: 'click', label: 'Click', color: '#00b85e', icon: '📱', number: 'click_blazeshop' },
  { id: 'payme', label: 'Payme', color: '#1cbce4', icon: '💰', number: 'payme_blazeshop' },
]

const AMOUNTS = [25000, 50000, 100000, 200000, 500000, 1000000]

export default function BalancePage() {
  const { user, deposits, loadDeposits, createDeposit, loading } = useStore()
  const [tab, setTab] = useState('deposit')
  const [step, setStep] = useState(1) // 1: amount, 2: method, 3: confirm
  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState(null)
  const [txid, setTxid] = useState('')
  const [promoCode, setPromoCode] = useState('')
  const { usePromo } = useStore()

  useEffect(() => { loadDeposits() }, [])

  const handleDeposit = async () => {
    const res = await createDeposit(parseInt(amount), method.id, txid)
    if (!res?.error) { setStep(1); setAmount(''); setMethod(null); setTxid('') }
  }

  const handlePromo = async () => {
    await usePromo(promoCode)
    setPromoCode('')
  }

  return (
    <div className="page" style={{ padding: '16px 16px 0' }}>
      <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>💰 Balans</div>

      {/* Balance display */}
      <div style={{
        background: 'linear-gradient(135deg,rgba(255,107,0,0.2),rgba(255,107,0,0.05))',
        border: '1px solid rgba(255,107,0,0.3)', borderRadius: 20, padding: '20px 20px', marginBottom: 20, marginTop: 14
      }}>
        <div style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Joriy balans</div>
        <div style={{ fontSize: 34, fontWeight: 900, color: '#FF6B00', marginBottom: 4 }}>
          {(user?.balance || 0).toLocaleString()} <span style={{ fontSize: 18, fontWeight: 600 }}>so'm</span>
        </div>
        <div style={{ fontSize: 12, color: '#888' }}>Jami sarflangan: {(user?.total_spent || 0).toLocaleString()} so'm</div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 4 }}>
        {[
          { val: 'deposit', label: '+ To\'ldirish' },
          { val: 'history', label: '📋 Tarix' },
          { val: 'promo', label: '🎟 Promo' },
        ].map(t => (
          <button key={t.val} onClick={() => setTab(t.val)} style={{
            flex: 1, padding: '10px 6px', borderRadius: 10, fontSize: 12, fontWeight: 600,
            cursor: 'pointer', border: 'none', transition: 'all .2s',
            background: tab === t.val ? 'linear-gradient(135deg,#FF6B00,#FF8C00)' : 'transparent',
            color: tab === t.val ? '#fff' : '#888'
          }}>{t.label}</button>
        ))}
      </div>

      {/* DEPOSIT TAB */}
      {tab === 'deposit' && (
        <div>
          {/* Step indicator */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24, gap: 0 }}>
            {[1,2,3].map((s, i) => (
              <React.Fragment key={s}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 800, flexShrink: 0,
                  background: step >= s ? 'linear-gradient(135deg,#FF6B00,#FF8C00)' : 'rgba(255,255,255,0.08)',
                  color: step >= s ? '#fff' : '#555', transition: 'all .3s'
                }}>{s}</div>
                {i < 2 && <div style={{ flex: 1, height: 2, background: step > s ? '#FF6B00' : 'rgba(255,255,255,0.08)', transition: 'background .3s' }}/>}
              </React.Fragment>
            ))}
          </div>

          {step === 1 && (
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>💵 Summa tanlang</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 16 }}>
                {AMOUNTS.map(a => (
                  <button key={a} onClick={() => setAmount(String(a))} style={{
                    padding: '12px 8px', borderRadius: 12, fontSize: 13, fontWeight: 700,
                    cursor: 'pointer', border: `1px solid ${amount == a ? 'rgba(255,107,0,0.5)' : 'rgba(255,255,255,0.08)'}`,
                    background: amount == a ? 'rgba(255,107,0,0.15)' : 'rgba(255,255,255,0.04)',
                    color: amount == a ? '#FF6B00' : '#ccc', transition: 'all .15s'
                  }}>{(a/1000).toFixed(0)}K</button>
                ))}
              </div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>Yoki o'zingiz kiriting:</div>
                <input className="input-field" type="number" value={amount} onChange={e => setAmount(e.target.value)}
                  placeholder="Summa (so'm)" style={{ textAlign: 'center', fontSize: 18, fontWeight: 700 }}/>
              </div>
              <div style={{ fontSize: 12, color: '#888', marginBottom: 20 }}>Minimal: 10,000 so'm · Maksimal: 5,000,000 so'm</div>
              <button className="btn-primary" onClick={() => setStep(2)} disabled={!amount || parseInt(amount) < 10000}
                style={{ opacity: (!amount || parseInt(amount) < 10000) ? 0.5 : 1 }}>
                Davom etish →
              </button>
            </div>
          )}

          {step === 2 && (
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>💳 To'lov usuli</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
                {METHODS.map(m => (
                  <div key={m.id} onClick={() => setMethod(m)} style={{
                    display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
                    borderRadius: 14, cursor: 'pointer', transition: 'all .15s',
                    background: method?.id === m.id ? `${m.color}15` : 'rgba(255,255,255,0.04)',
                    border: `2px solid ${method?.id === m.id ? m.color : 'rgba(255,255,255,0.07)'}`,
                  }}>
                    <div style={{ width: 42, height: 42, borderRadius: 12, background: `${m.color}20`, border: `1px solid ${m.color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>{m.icon}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 15, fontWeight: 700 }}>{m.label}</div>
                      <div style={{ fontSize: 11, color: '#888', fontFamily: 'monospace' }}>{m.number}</div>
                    </div>
                    {method?.id === m.id && <div style={{ fontSize: 20 }}>✅</div>}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setStep(1)}>← Orqaga</button>
                <button className="btn-primary" style={{ flex: 2 }} onClick={() => setStep(3)} disabled={!method}>
                  Davom etish →
                </button>
              </div>
            </div>
          )}

          {step === 3 && method && (
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>✅ Tasdiqlash</div>
              {/* Payment instruction */}
              <div style={{ background: `${method.color}12`, border: `1px solid ${method.color}30`, borderRadius: 16, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, color: '#fff' }}>To'lov ma'lumotlari</div>
                <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>Quyidagi raqamga pul o'tkazing:</div>
                <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'monospace', color: '#fff', background: 'rgba(255,255,255,0.08)', borderRadius: 10, padding: '10px 14px', marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {method.number}
                  <button onClick={() => {navigator.clipboard?.writeText(method.number)}} style={{ fontSize: 16, background: 'none', border: 'none', cursor: 'pointer' }}>📋</button>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: '#888' }}>Summa:</span>
                  <span style={{ fontSize: 14, fontWeight: 800, color: '#FF6B00' }}>{parseInt(amount).toLocaleString()} so'm</span>
                </div>
                <div style={{ fontSize: 11, color: '#888', marginTop: 10, lineHeight: 1.5 }}>
                  ⚠️ To'lov izohiga <strong style={{ color: '#fff' }}>Telegram ID: {user?.telegram_id}</strong> ni yozing
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>Tranzaksiya ID yoki chek raqamini kiriting:</div>
                <input className="input-field" value={txid} onChange={e => setTxid(e.target.value)}
                  placeholder="Masalan: 12345678"/>
              </div>

              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setStep(2)}>← Orqaga</button>
                <button className="btn-primary" style={{ flex: 2 }} onClick={handleDeposit}
                  disabled={!txid || loading.depositing}>
                  {loading.depositing ? '⏳...' : '📨 Yuborish'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* HISTORY TAB */}
      {tab === 'history' && (
        <div>
          {deposits.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#666' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>📋</div>
              <div style={{ fontSize: 16, fontWeight: 600 }}>Tarix bo'sh</div>
            </div>
          ) : (
            deposits.map(d => (
              <div key={d.id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '14px 16px', marginBottom: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 14 }}>
                      {METHODS.find(m => m.id === d.method)?.icon || '💳'}
                    </span>
                    <span style={{ fontSize: 14, fontWeight: 700 }}>{d.method.toUpperCase()}</span>
                    <span className={`badge-${d.status}`}>{
                      d.status === 'pending' ? 'Kutilmoqda' :
                      d.status === 'confirmed' ? 'Tasdiqlandi' : 'Rad etildi'
                    }</span>
                  </div>
                  <div style={{ fontSize: 11, color: '#888' }}>{d.created_at?.slice(0,16)}</div>
                  {d.admin_note && <div style={{ fontSize: 11, color: '#e74c3c', marginTop: 3 }}>{d.admin_note}</div>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 16, fontWeight: 800, color: d.status === 'confirmed' ? '#00d084' : d.status === 'rejected' ? '#e74c3c' : '#FF6B00' }}>
                    +{d.amount.toLocaleString()}
                  </div>
                  <div style={{ fontSize: 10, color: '#888' }}>so'm</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* PROMO TAB */}
      {tab === 'promo' && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <div style={{ fontSize: 52, marginBottom: 12 }}>🎟️</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Promo Kod</div>
            <div style={{ fontSize: 13, color: '#888' }}>Promo kodingizni kiriting va bonus oling!</div>
          </div>
          <input className="input-field" value={promoCode} onChange={e => setPromoCode(e.target.value.toUpperCase())}
            placeholder="PROMO KOD" style={{ textAlign: 'center', fontSize: 20, fontWeight: 800, letterSpacing: '.1em', marginBottom: 14 }}/>
          <button className="btn-primary" onClick={handlePromo} disabled={!promoCode}>
            🎁 Aktivlashtirish
          </button>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: 16, marginTop: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>ℹ️ Qanday olish mumkin?</div>
            {['Telegram kanaliga obuna bo\'ling', 'Referal havolangizni do\'stlaringizga ulashing', 'Aksiyalar va tanlovlarda qatnashing'].map((s, i) => (
              <div key={i} style={{ fontSize: 12, color: '#888', marginBottom: 8, display: 'flex', gap: 8 }}>
                <span>✅</span><span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
