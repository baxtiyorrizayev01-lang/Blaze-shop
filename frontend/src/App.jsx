import React, { useEffect } from 'react'
import useStore from './store/useStore'
import BottomNav from './components/BottomNav'
import Toast from './components/Toast'
import HomePage from './pages/HomePage'
import ShopPage from './pages/ShopPage'
import GiveawayPage from './pages/GiveawayPage'
import BalancePage from './pages/BalancePage'
import ProfilePage from './pages/ProfilePage'

export default function App() {
  const { activePage, initUser, loadFeatured, loadGiveaways, toast } = useStore()

  useEffect(() => {
    initUser()
    loadFeatured()
    loadGiveaways()
  }, [])

  const pages = {
    home: HomePage,
    shop: ShopPage,
    giveaway: GiveawayPage,
    balance: BalancePage,
    profile: ProfilePage,
  }
  const PageComponent = pages[activePage] || HomePage

  return (
    <div className="min-h-screen pb-20" style={{ background: '#0B0F17' }}>
      <PageComponent />
      <BottomNav />
      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  )
}
