import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/index.css'

// Aggressively unregister any existing service workers to prevent caching issues
if ('serviceWorker' in navigator) {
  // Unregister all service workers
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    registrations.forEach((registration) => {
      registration.unregister().then((success) => {
        if (success) {
          console.log('[Service Worker] Unregistered successfully')
        }
      }).catch((err) => {
        console.warn('[Service Worker] Error unregistering:', err)
      })
    })
  }).catch((err) => {
    console.warn('[Service Worker] Error getting registrations:', err)
  })
  
  // Clear all caches
  if ('caches' in window) {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.delete(cacheName).then((success) => {
            if (success) {
              console.log(`[Cache] Deleted cache: ${cacheName}`)
            }
          })
        })
      )
    }).catch((err) => {
      console.warn('[Cache] Error clearing caches:', err)
    })
  }
  
  // Also try to unregister via controller
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' })
  }
  
  // Add event listener to handle new service workers
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    window.location.reload()
  })
}

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

