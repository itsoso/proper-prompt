import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  FileText,
  BarChart3,
  Scale,
  Key,
  Settings,
  Menu,
  X,
  Sparkles,
  LogOut,
  User,
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { useAuthStore } from '../stores/authStore'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: '控制台' },
  { path: '/groups', icon: Users, label: '群组管理' },
  { path: '/prompts', icon: FileText, label: 'Prompt模板' },
  { path: '/analysis', icon: BarChart3, label: '群聊分析' },
  { path: '/evaluations', icon: Scale, label: 'Prompt评测' },
  { path: '/api-keys', icon: Key, label: 'API密钥' },
  { path: '/settings', icon: Settings, label: '设置' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    toast.success('已安全退出')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-dark-950 bg-grid">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed left-0 top-0 h-full bg-dark-900/95 backdrop-blur-xl border-r border-dark-700',
          'transition-all duration-300 z-50',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-dark-700">
          <motion.div
            className="flex items-center gap-3"
            initial={false}
            animate={{ opacity: sidebarOpen ? 1 : 0 }}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            {sidebarOpen && (
              <span className="font-display font-bold text-lg gradient-text">
                Proper Prompts
              </span>
            )}
          </motion.div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-dark-700 text-dark-300 hover:text-white transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200',
                  'hover:bg-dark-700/50',
                  isActive
                    ? 'bg-gradient-to-r from-primary-500/20 to-accent-500/20 text-white border border-primary-500/30'
                    : 'text-dark-300 hover:text-white'
                )}
              >
                <item.icon className={clsx('w-5 h-5 flex-shrink-0', isActive && 'text-primary-400')} />
                {sidebarOpen && (
                  <span className="font-medium">{item.label}</span>
                )}
                {isActive && sidebarOpen && (
                  <motion.div
                    className="ml-auto w-2 h-2 rounded-full bg-primary-500"
                    layoutId="activeIndicator"
                  />
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="p-4 rounded-xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 border border-dark-600">
              <p className="text-xs text-dark-400">版本 1.0.0</p>
              <p className="text-xs text-dark-500 mt-1">© 2024 Proper Prompts</p>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main
        className={clsx(
          'min-h-screen transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        {/* Header */}
        <header className="h-16 border-b border-dark-700 bg-dark-900/50 backdrop-blur-xl sticky top-0 z-40">
          <div className="flex items-center justify-between h-full px-6">
            <h1 className="text-xl font-semibold text-white">
              {navItems.find((item) => item.path === location.pathname)?.label || '控制台'}
            </h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800 border border-dark-600">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-dark-300">系统正常</span>
              </div>
              
              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800 border border-dark-600 hover:border-primary-500/50 transition-colors"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm text-white hidden md:block">
                    {user?.full_name || user?.username || 'Admin'}
                  </span>
                </button>
                
                {showUserMenu && (
                  <>
                    <div 
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    />
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute right-0 mt-2 w-48 py-2 bg-dark-800 border border-dark-600 rounded-lg shadow-xl z-50"
                    >
                      <div className="px-4 py-2 border-b border-dark-600">
                        <p className="text-sm font-medium text-white">{user?.username}</p>
                        <p className="text-xs text-dark-400">{user?.email || '管理员'}</p>
                      </div>
                      <button
                        onClick={handleLogout}
                        className="w-full px-4 py-2 text-left text-sm text-dark-300 hover:bg-dark-700 hover:text-white flex items-center gap-2"
                      >
                        <LogOut className="w-4 h-4" />
                        退出登录
                      </button>
                    </motion.div>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Outlet />
          </motion.div>
        </div>
      </main>
    </div>
  )
}

