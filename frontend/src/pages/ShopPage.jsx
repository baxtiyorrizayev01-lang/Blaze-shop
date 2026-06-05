import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { SkinSVG, SKIN_COLORS } from '../components/SkinCard'

const WEAPONS = ['Hammasi', 'Rifle', 'Sniper Rifle', 'Pistol', 'Knife']
const SORTS = [
  { val: 'newest', label: 'Yangi' },
  { val: 'price_asc', label: 'Arzon' },
  { val: 'price_desc', label: 'Qimmat' },
  { val: 'featured', label: 'Featured' },
]

export default function ShopPage() {
  const { skins, favorites, loadSkins, toggleFavorite, loading, showToast } = useStore()
  const [search, setSearch] = useState('')
  const [weapon, setWeapon] = useState('Hammasi')
  const [sort, setSort] = useState('newest')
  const [selectedSkin, setSelectedSkin] = useState(null)
  const [searchTimer, setSearchTimer] = useState(null)

  useEffect(() => {
    loadSkins({ weapon_type: weapon === 'Hammasi' ? null : weapon, sort })
  }, [weapon, sort])

  const handleSearch = (v) => {
    setSearch(v)
    clearTimeout(searchTimer)
    setSearchTimer(setTimeout(() => {
      loadSkins({ search: v || null, weapon_type: weapon === 'Hammasi' ? null : weapon, sort })
    }, 400))
  }

  const favIds = new Set(favorites.map(f => f.id))

  if (selectedSkin) return <SkinDetailPage skin={selectedSkin} onBack={() => setSelectedSkin(null)} isFav={favIds.has(selectedSkin.id)} />

  return (
    <div className="page" style={{ padding: '16px 16px 0' }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 14 }}>🛒 Shop</div>
        <div style={{ position: 'relative', marginBottom: 12 }}>
          <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 16 }}>🔍</span>
          <input className="input-field" value={search} onChange={e => handleSearch(e.target.value)}
            placeholder="Skin qidirish..." style={{ paddingLeft: 42 }}/>
        </div>
        {/* Weapon filter */}
        <div className="scroll-x" style={{ marginBottom: 12 }}>
          {WEAPONS.map(w => (
            <button key={w} onClick={() => setWeapon(w)} style={{
              padding: '7px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              whiteSpace: 'nowrap', cursor: 'pointer', border: 'none', flexShrink: 0,
              background: weapon === w ? 'linear-gradient(135deg,#FF6B00,#FF8C00)' : 'rgba(255,255,255,0.07)',
              color: weapon === w ? '#fff' : '#888', transition: 'all .15s'
            }}>{w}</button>
          ))}
        </div>
        {/* Sort */}
        <div style={{ display: 'flex', gap: 7 }}>
          {SORTS.map(s => (
            <button key={s.val} onClick={() => setSort(s.val)} style={{
              padding: '6px 12px', borderRadius: 10, fontSize: 11, fontWeight: 600,
              cursor: 'pointer', border: `1px solid ${sort === s.val ? 'rgba(255,107,0,0.5)' : 'rgba(255,255,255,0.08)'}`,
              background: sort === s.val ? 'rgba(255,107,0,0.15)' : 'rgba(255,255,255,0.04)',
              color: sort === s.val ? '#FF6B00' : '#888'
            }}>{s.label}</button>
          ))}
        </div>
      </div>

      {/* Skin grid */}
      {loading.skins ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="shimmer" style={{ borderRadius: 16, height: 200 }}/>
          ))}
        </div>
      ) : skins.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#666' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🔍</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>Skin topilmadi</div>
          <div style={{ fontSize: 13, marginTop: 6 }}>Boshqa kalit so'z kiriting</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, paddingBottom: 16 }}>
          {skins.map(skin => (
            <SkinGridCard key={skin.id} skin={skin} isFav={favIds.has(skin.id)}
              onFav={async (e) => { e.stopPropagation(); await toggleFavorite(skin.id) }}
              onClick={() => setSelectedSkin(skin)}/>
          ))}
        </div>
      )}
    </div>
  )
}

function SkinGridCard({ skin, isFav, onFav, onClick }) {
  const c = SKIN_COLORS[skin.weapon_type] || SKIN_COLORS.default
  return (
    <div className="skin-card" onClick={onClick}>
      <div style={{ background: `${c}12`, padding: 12, position: 'relative', display: 'flex', justifyContent: 'center' }}>
        {skin.is_featured && (
          <div style={{ position: 'absolute', top: 6, left: 6, background: 'rgba(255,107,0,0.9)', borderRadius: 5, padding: '1px 6px', fontSize: 8, fontWeight: 800 }}>HOT</div>
        )}
        <button onClick={onFav} style={{
          position: 'absolute', top: 6, right: 6, background: 'rgba(0,0,0,0.4)',
          border: 'none', borderRadius: 8, width: 28, height: 28,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', fontSize: 14
        }}>{isFav ? '❤️' : '🤍'}</button>
        <SkinSVG color={c} w={130} h={75}/>
      </div>
      <div style={{ padding: '10px 11px' }}>
        <div style={{ fontSize: 10, color: '#888', marginBottom: 2 }}>{skin.weapon_type}</div>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#fff', marginBottom: 2, lineHeight: 1.3,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{skin.name}</div>
        <div style={{ fontSize: 10, color: '#3498db', marginBottom: 7 }}>{skin.exterior}</div>
        <div style={{ fontSize: 13, color: '#FF6B00', fontWeight: 800 }}>{skin.price.toLocaleString()}<span style={{ fontSize: 9, fontWeight: 600, marginLeft: 2 }}>so'm</span></div>
      </div>
    </div>
  )
}

function SkinDetailPage({ skin, onBack, isFav }) {
  const { buyNow, toggleFavorite, loading, user } = useStore()
  const [fav, setFav] = useState(isFav)
  const [buying, setBuying] = useState(false)
  const c = SKIN_COLORS[skin.weapon_type] || SKIN_COLORS.default
  const canAfford = (user?.balance || 0) >= skin.price

  const handleBuy = async () => {
    if (!canAfford) return
    setBuying(true)
    const res = await buyNow(skin.id)
    setBuying(false)
    if (!res?.error) onBack()
  }

  const handleFav = async () => {
    const res = await toggleFavorite(skin.id)
    setFav(res)
  }

  return (
    <div className="page" style={{ minHeight: '100vh', background: '#0B0F17' }}>
      {/* Back */}
      <div style={{ padding: '16px 16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button onClick={onBack} style={{ background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '8px 14px', color: '#ccc', cursor: 'pointer', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
          ← Orqaga
        </button>
        <button onClick={handleFav} style={{ background: fav ? 'rgba(231,76,60,0.15)' : 'rgba(255,255,255,0.07)', border: `1px solid ${fav ? 'rgba(231,76,60,0.4)' : 'rgba(255,255,255,0.1)'}`, borderRadius: 12, padding: '8px 14px', cursor: 'pointer', fontSize: 18 }}>
          {fav ? '❤️' : '🤍'}
        </button>
      </div>

      {/* Preview */}
      <div style={{
        margin: '16px', borderRadius: 20, padding: '30px 20px',
        background: `linear-gradient(135deg, ${c}20, ${c}05)`,
        border: `1px solid ${c}30`, display: 'flex', justifyContent: 'center',
        position: 'relative', overflow: 'hidden'
      }}>
        <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at center, ${c}15 0%, transparent 70%)` }}/>
        <SkinSVG color={c} w={280} h={160}/>
      </div>

      <div style={{ padding: '0 16px 100px' }}>
        {/* Name & price */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: '#888', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 4 }}>{skin.weapon_type} · {skin.collection || 'Collection'}</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#fff', marginBottom: 8 }}>{skin.name}</div>
          <div style={{ fontSize: 30, fontWeight: 900, color: '#FF6B00' }}>{skin.price.toLocaleString()} <span style={{ fontSize: 16, fontWeight: 600 }}>so'm</span></div>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 18 }}>
          {[
            { l: 'Holat', v: skin.exterior },
            { l: 'Float', v: skin.float_val?.toFixed(4) || '—' },
            { l: 'Pattern', v: skin.pattern || '—' },
          ].map(({ l, v }) => (
            <div key={l} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '12px 10px', textAlign: 'center' }}>
              <div style={{ fontSize: 10, color: '#888', marginBottom: 5 }}>{l}</div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{v}</div>
            </div>
          ))}
        </div>

        {/* Details */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Batafsil ma'lumot</div>
          {[
            ['Tur', skin.weapon_type],
            ['Qurol', skin.name.split(' | ')[0]],
            ["To'plam", skin.collection || '—'],
            ["Holat", skin.exterior],
            ["Stok", `${skin.stock} ta mavjud`],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ fontSize: 13, color: '#888' }}>{k}</span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>

        {/* Balance warning */}
        {!canAfford && (
          <div style={{ background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.3)', borderRadius: 12, padding: '12px 14px', marginBottom: 14, fontSize: 13, color: '#e74c3c', display: 'flex', gap: 8, alignItems: 'center' }}>
            ⚠️ Balansingiz yetarli emas. Iltimos, balansni to'ldiring.
          </div>
        )}
      </div>

      {/* Buy button fixed */}
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, padding: '12px 16px', background: 'rgba(11,15,23,0.97)', borderTop: '1px solid rgba(255,255,255,0.07)', paddingBottom: 'calc(12px + env(safe-area-inset-bottom))' }}>
        <button className="btn-primary" onClick={handleBuy}
          disabled={!canAfford || buying || loading.buying}
          style={{ opacity: canAfford ? 1 : 0.5 }}>
          {buying || loading.buying ? '⏳ Yuklanmoqda...' : canAfford ? `🛒 Sotib olish — ${skin.price.toLocaleString()} so'm` : '💰 Balans yetarli emas'}
        </button>
      </div>
    </div>
  )
}
