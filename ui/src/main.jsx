import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/index.css'

// Aggressively unregister and disable service workers to prevent caching issues
(function() {
  if ('serviceWorker' in navigator) {
    // Override register to prevent any new registrations
    const originalRegister = navigator.serviceWorker.register.bind(navigator.serviceWorker)
    navigator.serviceWorker.register = function() {
      return Promise.reject(new Error('Service workers disabled'))
    }
    
    // Unregister all existing service workers
    const unregisterAll = () => {
      navigator.serviceWorker.getRegistrations().then((registrations) => {
        registrations.forEach((registration) => {
          registration.unregister().catch(() => {})
        })
      }).catch(() => {})
    }
    
    // Clear all caches
    const clearAllCaches = () => {
      if ('caches' in window) {
        caches.keys().then((names) => {
          names.forEach((name) => caches.delete(name).catch(() => {}))
        }).catch(() => {})
      }
    }
    
    // Execute immediately
    unregisterAll()
    clearAllCaches()
    
    // Also try to stop active service worker
    if (navigator.serviceWorker.controller) {
      try {
        navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' })
      } catch(e) {}
      navigator.serviceWorker.getRegistration().then((reg) => {
        if (reg) reg.unregister().catch(() => {})
      }).catch(() => {})
    }
    
    // Keep trying periodically to catch any that register later
    setInterval(() => {
      unregisterAll()
    }, 1000)
  }
})();

// Suppress chrome extension and service worker errors in console
(function() {
  const originalError = console.error
  const originalWarn = console.warn
  
  console.error = function(...args) {
    const message = String(args[0] || '')
    if (message.includes('chrome-extension://') || 
        message.includes('service-worker.js') ||
        message.includes('Failed to fetch') ||
        message.includes('ERR_FILE_NOT_FOUND')) {
      return // Suppress these errors
    }
    originalError.apply(console, args)
  }
  
  console.warn = function(...args) {
    const message = String(args[0] || '')
    if (message.includes('service-worker') || 
        message.includes('Returning from cache') ||
        message.includes('Returning from network')) {
      return // Suppress service worker warnings
    }
    originalWarn.apply(console, args)
  }
})();

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found!')
}

try {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
} catch (error) {
  console.error('Failed to render app:', error)
  rootElement.innerHTML = `
    <div style="padding: 20px; color: red;">
      <h1>Error Loading Application</h1>
      <p>${error.message}</p>
      <pre>${error.stack}</pre>
    </div>
  `
}

