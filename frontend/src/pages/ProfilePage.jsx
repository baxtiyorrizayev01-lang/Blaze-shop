import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'

const tg = window.Telegram?.WebApp

export default function ProfilePage() {
  const { user, orders, loadOrders, favorites, loadFavorites, referrals, loadReferrals, updateTradeUrl, notifications, loadNotifications } = useStore()
  const [tab, setTab] = useState('main')
  const [tradeUrl, setTradeUrl] = useState(user?.trade_url || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadOrders()
    loadFavorites()
    loadReferrals()
    loadNotifications()
  }, [])

  useEffect(() => {
    if (user?.trade_url) setTradeUrl(user.trade_url)
  }, [user])

  const handleSaveUrl = async () => {
    setSaving(true)
    await updateTradeUrl(tradeUrl)
    setSaving(false)
  }

  const copyRef = () => {
    const link = `https://t.me/blazecs2bot?start=ref_${referrals.code}`
    navigator.clipboard?.writeText(link)
    tg?.HapticFeedback?.notificationOccurred('success')
    useStore.getState().showToast('Havola nusxalandi!', 'success')
  }

  const unread = notifications.filter(n => !n.is_read).length

  return (
    <div className="page" style={{ padding: '16px 16px 0' }}>
      {/* Profile header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20, padding: '18px 18px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 20 }}>
        <div style={{
          width: 60, height: 60, borderRadius: 20, flexShrink: 0,
          background: 'linear-gradient(135deg,#FF6B00,#ff3300)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 26, fontWeight: 900, fontFamily: "'Barlow Condensed',sans-serif",
          boxShadow: '0 4px 20px rgba(255,107,0,0.4)'
        }}>
          {user?.first_name?.[0]?.toUpperCase() || 'B'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 18, fontWeight: 800, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.first_name || 'Foydalanuvchi'}</div>
          <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>@{user?.username || 'noma\'lum'}</div>
          <div style={{ fontSize: 11, color: '#666', fontFamily: 'monospace' }}>ID: {user?.telegram_id}</div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#FF6B00' }}>{(user?.balance || 0).toLocaleString()}</div>
          <div style={{ fontSize: 10, color: '#888' }}>so'm</div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 18 }}>
        {[
          { label: "Buyurtmalar", val: orders.length, icon: '🛒' },
          { label: "Sevimlilar", val: favorites.length, icon: '❤️' },
          { label: "Referallar", val: referrals.list?.length || 0, icon: '👥' },
        ].map(s => (
          <div key={s.label} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '12px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 22, marginBottom: 4 }}>{s.icon}</div>
            <div style={{ fontSize: 20, fontWeight: 800 }}>{s.val}</div>
            <div style={{ fontSize: 10, color: '#888' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="scroll-x" style={{ gap: 8, marginBottom: 18, paddingBottom: 2 }}>
        {[
          { val: 'main', label: '👤 Profil' },
          { val: 'orders', label: '🛒 Buyurtmalar' },
          { val: 'favorites', label: '❤️ Sevimlilar' },
          { val: 'referral', label: '👥 Referal' },
          { val: 'notifs', label: `🔔 Xabarlar${unread > 0 ? ` (${unread})` : ''}` },
        ].map(t => (
          <button key={t.val} onClick={() => setTab(t.val)} style={{
            padding: '8px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
            whiteSpace: 'nowrap', cursor: 'pointer', border: 'none', flexShrink: 0,
            background: tab === t.val ? 'linear-gradient(135deg,#FF6B00,#FF8C00)' : 'rgba(255,255,255,0.07)',
            color: tab === t.val ? '#fff' : '#888'
          }}>{t.label}</button>
        ))}
      </div>

      {/* MAIN TAB */}
      {tab === 'main' && (
        <div>
          {/* Trade URL */}
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 16, marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
              🔗 Trade URL
              <span style={{ fontSize: 10, color: user?.trade_url ? '#00d084' : '#e74c3c', fontWeight: 600, background: user?.trade_url ? 'rgba(0,208,132,0.1)' : 'rgba(231,76,60,0.1)', padding: '2px 7px', borderRadius: 10 }}>
                {user?.trade_url ? '✅ Saqlangan' : '❌ Kiritilmagan'}
              </span>
            </div>
            <input className="input-field" value={tradeUrl} onChange={e => setTradeUrl(e.target.value)}
              placeholder="https://steamcommunity.com/tradeoffer/new/..." style={{ marginBottom: 10, fontSize: 12 }}/>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 12, lineHeight: 1.5 }}>
              💡 Trade URL buyurtmangizni qabul qilish uchun kerak. Steam profilingizdan oling.
            </div>
            <button className="btn-primary" onClick={handleSaveUrl} disabled={saving} style={{ padding: '11px' }}>
              {saving ? '⏳ Saqlanmoqda...' : '💾 Saqlash'}
            </button>
          </div>

          {/* Menu items */}
          {[
            { icon: '📦', label: "Buyurtmalar tarixi", tab: 'orders' },
            { icon: '❤️', label: "Sevimli skinlar", tab: 'favorites' },
            { icon: '👥', label: "Referal dastur", tab: 'referral' },
            { icon: '🔔', label: `Xabarnomalar ${unread > 0 ? `(${unread})` : ''}`, tab: 'notifs' },
          ].map(item => (
            <div key={item.label} onClick={() => setTab(item.tab)} style={{
              display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
              background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 14, marginBottom: 10, cursor: 'pointer', transition: 'all .15s'
            }}>
              <span style={{ fontSize: 22 }}>{item.icon}</span>
              <span style={{ flex: 1, fontSize: 14, fontWeight: 600 }}>{item.label}</span>
              <span style={{ color: '#555', fontSize: 16 }}>›</span>
            </div>
          ))}

          {/* Support */}
          <div style={{ marginTop: 4 }}>
            <a href="https://t.me/blazecs2admin" target="_blank" style={{
              display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
              background: 'rgba(0,136,204,0.08)', border: '1px solid rgba(0,136,204,0.2)',
              borderRadius: 14, textDecoration: 'none', color: '#fff', marginBottom: 10
            }}>
              <span style={{ fontSize: 22 }}>💬</span>
              <span style={{ flex: 1, fontSize: 14, fontWeight: 600 }}>Qo'llab-quvvatlash</span>
              <span style={{ color: '#3498db', fontSize: 12, fontWeight: 600 }}>Telegram →</span>
            </a>
          </div>
        </div>
      )}

      {/* ORDERS TAB */}
      {tab === 'orders' && (
        <div>
          {orders.length === 0 ? (
            <EmptyState icon="🛒" text="Buyurtmalar yo'q" />
          ) : orders.map(o => (
            <div key={o.id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '14px 16px', marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 3 }}>{o.skin_name}</div>
                  <div style={{ fontSize: 11, color: '#888' }}>{o.exterior} · {o.weapon_type}</div>
                </div>
                <span className={`badge-${o.status}`}>{
                  o.status === 'pending' ? 'Kutilmoqda' :
                  o.status === 'delivered' ? 'Yetkazildi' :
                  o.status === 'cancelled' ? 'Bekor' : o.status
                }</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: 11, color: '#666' }}>#{o.id} · {o.created_at?.slice(0,10)}</div>
                <div style={{ fontSize: 15, fontWeight: 800, color: '#FF6B00' }}>{o.price.toLocaleString()} so'm</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* FAVORITES TAB */}
      {tab === 'favorites' && (
        <div>
          {favorites.length === 0 ? (
            <EmptyState icon="❤️" text="Sevimlilar ro'yxati bo'sh" />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {favorites.map(s => (
                <div key={s.id} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '12px', cursor: 'pointer' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>{s.name}</div>
                  <div style={{ fontSize: 10, color: '#888', marginBottom: 6 }}>{s.exterior}</div>
                  <div style={{ fontSize: 13, color: '#FF6B00', fontWeight: 800 }}>{s.price.toLocaleString()} so'm</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* REFERRAL TAB */}
      {tab === 'referral' && (
        <div>
          <div style={{ background: 'rgba(0,208,132,0.08)', border: '1px solid rgba(0,208,132,0.2)', borderRadius: 20, padding: 18, marginBottom: 16, textAlign: 'center' }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>👥</div>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Referal dasturi</div>
            <div style={{ fontSize: 13, color: '#888', marginBottom: 14, lineHeight: 1.5 }}>
              Har bir taklif qilgan do'stingiz uchun <strong style={{ color: '#00d084' }}>5,000 so'm</strong> bonus!
            </div>
            <div style={{ background: 'rgba(0,208,132,0.1)', border: '1px solid rgba(0,208,132,0.2)', borderRadius: 12, padding: '12px 16px', fontSize: 14, fontWeight: 700, marginBottom: 12, fontFamily: 'monospace', letterSpacing: '.05em' }}>
              {referrals.code || '...'}
            </div>
            <button className="btn-primary" onClick={copyRef} style={{ background: 'linear-gradient(135deg,#00d084,#00b872)', boxShadow: '0 4px 20px rgba(0,208,132,0.3)' }}>
              📋 Havolani nusxalash
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
            <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '14px', textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#00d084' }}>{referrals.list?.length || 0}</div>
              <div style={{ fontSize: 11, color: '#888' }}>Taklif qilinganlar</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '14px', textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#FF6B00' }}>{((referrals.list?.length || 0) * 5000).toLocaleString()}</div>
              <div style={{ fontSize: 11, color: '#888' }}>Bonus (so'm)</div>
            </div>
          </div>

          {referrals.list?.length > 0 && (
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Referallarim</div>
              {referrals.list.map((r, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ fontSize: 13 }}>@{r.username || r.first_name}</div>
                  <div style={{ fontSize: 11, color: '#888' }}>{r.created_at?.slice(0,10)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* NOTIFICATIONS TAB */}
      {tab === 'notifs' && (
        <div>
          {notifications.length === 0 ? (
            <EmptyState icon="🔔" text="Xabarnomalar yo'q" />
          ) : notifications.map(n => (
            <div key={n.id} style={{
              background: n.is_read ? 'rgba(255,255,255,0.03)' : 'rgba(255,107,0,0.08)',
              border: `1px solid ${n.is_read ? 'rgba(255,255,255,0.07)' : 'rgba(255,107,0,0.25)'}`,
              borderRadius: 14, padding: '14px 16px', marginBottom: 10
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{n.title}</div>
                {!n.is_read && <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#FF6B00', flexShrink: 0, marginTop: 4 }}/>}
              </div>
              <div style={{ fontSize: 12, color: '#888', lineHeight: 1.5 }}>{n.message}</div>
              <div style={{ fontSize: 10, color: '#666', marginTop: 6 }}>{n.created_at?.slice(0,16)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState({ icon, text }) {
  return (
    <div style={{ textAlign: 'center', padding: '60px 20px', color: '#666' }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 16, fontWeight: 600 }}>{text}</div>
    </div>
  )
}
