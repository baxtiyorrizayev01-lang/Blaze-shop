/**
 * Blaze CS2 Marketplace — Production Store
 * JWT auth + all API calls
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API = import.meta.env.VITE_API_URL || 'https://your-backend.railway.app'
const tg  = window.Telegram?.WebApp

// ── Haptics ──────────────────────────────────────────────────────────────────
export const haptic = {
  light:   () => tg?.HapticFeedback?.impactOccurred('light'),
  medium:  () => tg?.HapticFeedback?.impactOccurred('medium'),
  heavy:   () => tg?.HapticFeedback?.impactOccurred('heavy'),
  success: () => tg?.HapticFeedback?.notificationOccurred('success'),
  error:   () => tg?.HapticFeedback?.notificationOccurred('error'),
  warning: () => tg?.HapticFeedback?.notificationOccurred('warning'),
}

// ── API client ───────────────────────────────────────────────────────────────
let _token = null

async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...opts.headers }

  if (_token)                      headers['Authorization'] = `Bearer ${_token}`
  if (tg?.initData)                headers['X-Init-Data']   = tg.initData

  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

const get    = path          => apiFetch(path)
const post   = (path, body)  => apiFetch(path, { method: 'POST', body })
const patch  = (path, body)  => apiFetch(path, { method: 'PATCH', body })
const del    = path          => apiFetch(path, { method: 'DELETE' })

// ── Store ────────────────────────────────────────────────────────────────────
const useStore = create(
  persist(
    (set, getState) => ({
      // ── State ──────────────────────────────────────────────────────────────
      accessToken:    null,
      user:           null,
      skins:          [],
      featuredSkins:  [],
      giveaways:      [],
      orders:         [],
      deposits:       [],
      favorites:      new Set(),
      notifications:  [],
      unreadCount:    0,
      referrals:      { code: '', count: 0, earned: 0, link: '', referrals: [] },
      activePage:     'home',
      loading:        {},
      toast:          null,

      // ── Navigation ─────────────────────────────────────────────────────────
      setPage: page => {
        haptic.light()
        set({ activePage: page })
      },

      // ── Toast ──────────────────────────────────────────────────────────────
      showToast: (message, type = 'info') => {
        haptic[type === 'success' ? 'success' : type === 'error' ? 'error' : 'light']()
        set({ toast: { message, type, id: Date.now() } })
        setTimeout(() => set({ toast: null }), 3500)
      },

      setLoading: (key, val) => set(s => ({ loading: { ...s.loading, [key]: val } })),

      // ── Auth ───────────────────────────────────────────────────────────────
      initUser: async () => {
        set(s => ({ loading: { ...s.loading, user: true } }))
        try {
          // 1) Try JWT auth via Telegram initData
          if (tg?.initData) {
            const auth = await post('/api/auth/telegram', { init_data: tg.initData })
            _token = auth.access_token
            set({ accessToken: auth.access_token })
          } else if (getState().accessToken) {
            // Restore from persisted token
            _token = getState().accessToken
          }

          const user = await get('/api/users/me')
          set({ user })

          // Expand Telegram WebApp
          tg?.expand()
          tg?.setHeaderColor('#0B0F17')
          tg?.setBackgroundColor('#0B0F17')
        } catch (e) {
          console.warn('Auth failed:', e)
          // Dev mock
          set({ user: {
            id: 1, telegram_id: 12345678,
            username: 'blazeuser', first_name: 'Blaze',
            balance: 125000, role: 'user',
            referral_code: 'BLAZE001', total_spent: 65000,
            steam_id: null, trade_url: null,
          }})
        } finally {
          set(s => ({ loading: { ...s.loading, user: false } }))
        }
      },

      refreshUser: async () => {
        try {
          const user = await get('/api/users/me')
          set({ user })
        } catch (_) {}
      },

      // ── Skins ──────────────────────────────────────────────────────────────
      loadSkins: async (filters = {}) => {
        set(s => ({ loading: { ...s.loading, skins: true } }))
        try {
          const params = new URLSearchParams(
            Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
          ).toString()
          const data = await get(`/api/skins/?${params}`)
          set({ skins: data })
        } catch (e) {
          getState().showToast('Skinlarni yuklashda xato', 'error')
        } finally {
          set(s => ({ loading: { ...s.loading, skins: false } }))
        }
      },

      loadFeatured: async () => {
        try {
          const data = await get('/api/skins/featured')
          set({ featuredSkins: data })
        } catch (_) {}
      },

      toggleFavorite: async skinId => {
        try {
          const res = await post(`/api/skins/${skinId}/favorite`)
          set(s => {
            const favs = new Set(s.favorites)
            res.is_favorite ? favs.add(skinId) : favs.delete(skinId)
            return { favorites: favs }
          })
          haptic[res.is_favorite ? 'success' : 'light']()
        } catch (_) {}
      },

      loadFavorites: async () => {
        try {
          const data = await get('/api/skins/user/favorites')
          set({ favorites: new Set(data.map(s => s.id)) })
        } catch (_) {}
      },

      // ── Giveaways ──────────────────────────────────────────────────────────
      loadGiveaways: async () => {
        try {
          const data = await get('/api/giveaways/')
          set({ giveaways: data })
        } catch (_) {}
      },

      joinGiveaway: async id => {
        set(s => ({ loading: { ...s.loading, giveaway: true } }))
        try {
          await post(`/api/giveaways/${id}/join`)
          haptic.success()
          getState().showToast("🎉 Giveaway'ga qo'shildingiz!", 'success')
          return true
        } catch (e) {
          getState().showToast(e.message, 'error')
          return false
        } finally {
          set(s => ({ loading: { ...s.loading, giveaway: false } }))
        }
      },

      // ── Orders ─────────────────────────────────────────────────────────────
      buySkin: async (skinId, tradeUrl) => {
        set(s => ({ loading: { ...s.loading, buy: true } }))
        try {
          const res = await post('/api/orders/buy', { skin_id: skinId, trade_url: tradeUrl })
          haptic.success()
          getState().showToast('✅ Buyurtma qabul qilindi!', 'success')
          await getState().refreshUser()
          return { ok: true, order_id: res.order_id }
        } catch (e) {
          haptic.error()
          getState().showToast(e.message, 'error')
          return { ok: false, error: e.message }
        } finally {
          set(s => ({ loading: { ...s.loading, buy: false } }))
        }
      },

      loadOrders: async () => {
        set(s => ({ loading: { ...s.loading, orders: true } }))
        try {
          const data = await get('/api/orders/')
          set({ orders: data })
        } catch (_) {}
        finally { set(s => ({ loading: { ...s.loading, orders: false } })) }
      },

      // ── Deposits ───────────────────────────────────────────────────────────
      initDeposit: async (amount, method) => {
        set(s => ({ loading: { ...s.loading, deposit: true } }))
        try {
          const res = await post('/api/deposits/init', { amount, method })
          return res
        } catch (e) {
          getState().showToast(e.message, 'error')
          return null
        } finally {
          set(s => ({ loading: { ...s.loading, deposit: false } }))
        }
      },

      submitManualDeposit: async (amount, method, transaction_id) => {
        set(s => ({ loading: { ...s.loading, deposit: true } }))
        try {
          await post('/api/deposits/manual', { amount, method, transaction_id })
          haptic.success()
          getState().showToast("To'lov so'rovi yuborildi!", 'success')
          return true
        } catch (e) {
          haptic.error()
          getState().showToast(e.message, 'error')
          return false
        } finally {
          set(s => ({ loading: { ...s.loading, deposit: false } }))
        }
      },

      loadDeposits: async () => {
        try {
          const data = await get('/api/deposits/')
          set({ deposits: data })
        } catch (_) {}
      },

      // ── Referrals ──────────────────────────────────────────────────────────
      loadReferrals: async () => {
        try {
          const data = await get('/api/users/referrals')
          set({ referrals: data })
        } catch (_) {}
      },

      // ── Daily bonus ────────────────────────────────────────────────────────
      claimDailyBonus: async () => {
        try {
          const res = await post('/api/users/daily-bonus')
          haptic.success()
          getState().showToast(`🎁 +${res.amount.toLocaleString()} so'm! ${res.streak} kun ketma-ket`, 'success')
          await getState().refreshUser()
          return res
        } catch (e) {
          haptic.warning()
          getState().showToast(e.message, 'warning')
          return null
        }
      },

      // ── Promo ──────────────────────────────────────────────────────────────
      usePromo: async code => {
        try {
          const res = await post(`/api/users/promo?code=${encodeURIComponent(code)}`)
          haptic.success()
          getState().showToast(`🎟 +${res.amount.toLocaleString()} so'm!`, 'success')
          await getState().refreshUser()
          return true
        } catch (e) {
          haptic.error()
          getState().showToast(e.message, 'error')
          return false
        }
      },

      // ── Profile ────────────────────────────────────────────────────────────
      updateTradeUrl: async url => {
        try {
          await patch('/api/users/me', { trade_url: url })
          set(s => ({ user: { ...s.user, trade_url: url } }))
          haptic.success()
          getState().showToast('Trade URL saqlandi!', 'success')
          return true
        } catch (e) {
          getState().showToast(e.message, 'error')
          return false
        }
      },

      // ── Steam ──────────────────────────────────────────────────────────────
      linkSteam: async () => {
        try {
          const res = await get('/api/auth/steam/login')
          if (res.redirect_url) {
            tg?.openLink(res.redirect_url)
          }
        } catch (e) {
          getState().showToast(e.message, 'error')
        }
      },

      unlinkSteam: async () => {
        try {
          await del('/api/auth/steam/unlink')
          set(s => ({ user: { ...s.user, steam_id: null, steam_username: null, steam_avatar: null } }))
          getState().showToast('Steam akkaunt uzildi', 'info')
        } catch (e) {
          getState().showToast(e.message, 'error')
        }
      },

      loadInventory: async () => {
        set(s => ({ loading: { ...s.loading, inventory: true } }))
        try {
          const data = await get('/api/steam/inventory')
          return data
        } catch (e) {
          getState().showToast(e.message, 'error')
          return null
        } finally {
          set(s => ({ loading: { ...s.loading, inventory: false } }))
        }
      },

      // ── Notifications ──────────────────────────────────────────────────────
      loadNotifications: async () => {
        try {
          const data = await get('/api/users/notifications')
          set({ notifications: data })
          const uc = await get('/api/users/notifications/unread-count')
          set({ unreadCount: uc.count })
        } catch (_) {}
      },

      checkChannelSubscription: async () => {
        try {
          const res = await get('/api/telegram/channel/check')
          return res.subscribed
        } catch (_) { return false }
      },
    }),
    {
      name: 'blaze-store',
      partialize: s => ({ accessToken: s.accessToken }),
    }
  )
)

// Sync token from persisted storage
const stored = useStore.getState().accessToken
if (stored) _token = stored

export default useStore
