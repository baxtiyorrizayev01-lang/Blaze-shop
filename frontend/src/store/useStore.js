import { create } from 'zustand'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8080/api'
const tg = window.Telegram?.WebApp

export const haptic = {
  light: () => tg?.HapticFeedback?.impactOccurred('light'),
  medium: () => tg?.HapticFeedback?.impactOccurred('medium'),
  heavy: () => tg?.HapticFeedback?.impactOccurred('heavy'),
  success: () => tg?.HapticFeedback?.notificationOccurred('success'),
  error: () => tg?.HapticFeedback?.notificationOccurred('error'),
  warning: () => tg?.HapticFeedback?.notificationOccurred('warning'),
}

async function api(action, data = {}) {
  const tgUser = tg?.initDataUnsafe?.user
  const telegram_id = tgUser?.id || 12345678 // fallback for dev
  try {
    const res = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, telegram_id, ...data })
    })
    return await res.json()
  } catch (e) {
    console.error('API error:', e)
    return { error: 'Server bilan bog\'lanib bo\'lmadi' }
  }
}

const useStore = create((set, get) => ({
  // State
  user: null,
  skins: [],
  featuredSkins: [],
  giveaways: [],
  orders: [],
  deposits: [],
  favorites: [],
  notifications: [],
  referrals: { list: [], code: '' },
  activePage: 'home',
  loading: {},
  toast: null,

  // Navigation
  setPage: (page) => {
    haptic.light()
    set({ activePage: page })
  },

  // Toast
  showToast: (message, type = 'info') => {
    haptic[type === 'success' ? 'success' : type === 'error' ? 'error' : 'light']()
    set({ toast: { message, type } })
    setTimeout(() => set({ toast: null }), 3000)
  },

  setLoading: (key, val) => set(s => ({ loading: { ...s.loading, [key]: val } })),

  // Init user
  initUser: async () => {
    const tgUser = tg?.initDataUnsafe?.user
    set({ loading: { ...get().loading, user: true } })
    // First sync with backend
    if (tgUser) {
      await api('get_user', {})
    }
    const res = await api('get_user')
    if (res.user) set({ user: res.user })
    else {
      // Dev mock user
      set({ user: {
        id: 1, telegram_id: 12345678,
        username: 'blazeuser', first_name: 'Blaze',
        balance: 125000, referral_code: 'BLAZE001',
        total_spent: 65000, is_admin: 0
      }})
    }
    set(s => ({ loading: { ...s.loading, user: false } }))
  },

  // Skins
  loadSkins: async (filters = {}) => {
    set(s => ({ loading: { ...s.loading, skins: true } }))
    const res = await api('get_skins', filters)
    if (res.skins) set({ skins: res.skins })
    set(s => ({ loading: { ...s.loading, skins: false } }))
  },

  loadFeatured: async () => {
    const res = await api('get_featured')
    if (res.skins) set({ featuredSkins: res.skins })
  },

  // Giveaways
  loadGiveaways: async () => {
    const res = await api('get_giveaways', { status: 'active' })
    if (res.giveaways) set({ giveaways: res.giveaways })
  },

  joinGiveaway: async (giveaway_id) => {
    set(s => ({ loading: { ...s.loading, joining: true } }))
    const res = await api('join_giveaway', { giveaway_id })
    set(s => ({ loading: { ...s.loading, joining: false } }))
    if (res.error) get().showToast(res.error, 'error')
    else { get().showToast('Giveawayga qo\'shildingiz! 🎉', 'success'); get().loadGiveaways() }
    return res
  },

  // Orders
  loadOrders: async () => {
    const res = await api('get_orders')
    if (res.orders) set({ orders: res.orders })
  },

  buyNow: async (skin_id) => {
    set(s => ({ loading: { ...s.loading, buying: true } }))
    const res = await api('buy_skin', { skin_id })
    set(s => ({ loading: { ...s.loading, buying: false } }))
    if (res.error) get().showToast(res.error, 'error')
    else {
      get().showToast('Buyurtma qabul qilindi! ✅', 'success')
      get().initUser()
      get().loadOrders()
    }
    return res
  },

  // Deposits
  loadDeposits: async () => {
    const res = await api('get_deposits')
    if (res.deposits) set({ deposits: res.deposits })
  },

  createDeposit: async (amount, method, transaction_id) => {
    set(s => ({ loading: { ...s.loading, depositing: true } }))
    const res = await api('deposit', { amount, method, transaction_id })
    set(s => ({ loading: { ...s.loading, depositing: false } }))
    if (res.error) get().showToast(res.error, 'error')
    else { get().showToast('To\'lov so\'rovi yuborildi! ⏳', 'success'); get().loadDeposits() }
    return res
  },

  // Favorites
  loadFavorites: async () => {
    const res = await api('get_favorites')
    if (res.favorites) set({ favorites: res.favorites })
  },

  toggleFavorite: async (skin_id) => {
    const res = await api('toggle_favorite', { skin_id })
    await get().loadFavorites()
    return res.is_favorite
  },

  // Referrals
  loadReferrals: async () => {
    const res = await api('get_referrals')
    if (res) set({ referrals: { list: res.referrals || [], code: res.code || '' } })
  },

  // Promo
  usePromo: async (code) => {
    const res = await api('use_promo', { code })
    if (res.error) get().showToast(res.error, 'error')
    else {
      get().showToast(`+${res.amount?.toLocaleString()} so'm qo'shildi! 🎉`, 'success')
      get().initUser()
    }
    return res
  },

  // Notifications
  loadNotifications: async () => {
    const res = await api('get_notifications')
    if (res.notifications) set({ notifications: res.notifications })
  },

  // Trade URL
  updateTradeUrl: async (trade_url) => {
    const res = await api('update_trade_url', { trade_url })
    if (!res.error) get().showToast('Trade URL yangilandi!', 'success')
  },
}))

export default useStore
