import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'
import { TranslationProvider } from './contexts/TranslationContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TranslationProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </TranslationProvider>
  </React.StrictMode>,
)
