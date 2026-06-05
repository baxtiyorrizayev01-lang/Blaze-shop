import React from 'react'
import useStore from '../store/useStore'

const tabs = [
  { id: 'home', label: 'Bosh sahifa', icon: HomeIcon },
  { id: 'shop', label: 'Shop', icon: ShopIcon },
  { id: 'giveaway', label: 'Giveaway', icon: GiftIcon },
  { id: 'balance', label: 'Balans', icon: WalletIcon },
  { id: 'profile', label: 'Profil', icon: UserIcon },
]

function HomeIcon({ active }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#FF6B00' : 'none'}
    stroke={active ? '#FF6B00' : '#555'} strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
    <polyline points="9,22 9,12 15,12 15,22"/>
  </svg>
}
function ShopIcon({ active }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#FF6B00' : 'none'}
    stroke={active ? '#FF6B00' : '#555'} strokeWidth="2">
    <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
    <line x1="3" y1="6" x2="21" y2="6"/>
    <path d="M16 10a4 4 0 01-8 0"/>
  </svg>
}
function GiftIcon({ active }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#FF6B00' : 'none'}
    stroke={active ? '#FF6B00' : '#555'} strokeWidth="2">
    <polyline points="20,12 20,22 4,22 4,12"/>
    <rect x="2" y="7" width="20" height="5"/>
    <line x1="12" y1="22" x2="12" y2="7"/>
    <path d="M12 7H7.5a2.5 2.5 0 010-5C11 2 12 7 12 7z"/>
    <path d="M12 7h4.5a2.5 2.5 0 000-5C13 2 12 7 12 7z"/>
  </svg>
}
function WalletIcon({ active }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#FF6B00' : 'none'}
    stroke={active ? '#FF6B00' : '#555'} strokeWidth="2">
    <rect x="1" y="4" width="22" height="16" rx="2"/>
    <line x1="1" y1="10" x2="23" y2="10"/>
    <circle cx="17" cy="15" r="1" fill={active ? '#FF6B00' : '#555'}/>
  </svg>
}
function UserIcon({ active }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#FF6B00' : 'none'}
    stroke={active ? '#FF6B00' : '#555'} strokeWidth="2">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
}

export default function BottomNav() {
  const { activePage, setPage } = useStore()
  return (
    <nav className="bottom-nav">
      <div style={{ display: 'flex' }}>
        {tabs.map(tab => {
          const active = activePage === tab.id
          return (
            <div key={tab.id} className={`nav-item ${active ? 'active' : ''}`}
              onClick={() => setPage(tab.id)}>
              <div className="nav-icon"><tab.icon active={active} /></div>
              <span className="nav-label">{tab.label}</span>
            </div>
          )
        })}
      </div>
    </nav>
  )
}
