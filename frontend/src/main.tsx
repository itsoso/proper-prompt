import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'
import { debugLog } from './utils/debug'

// Initialize debug logging
debugLog.info('Application starting...')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster 
          position="top-right"
          toastOptions={{
            className: 'bg-dark-800 text-white border border-dark-600',
            duration: 4000,
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)

debugLog.info('Application rendered')

