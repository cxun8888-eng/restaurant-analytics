import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './styles/tokens.css'
import './styles/workspace.css'
import './styles/anomalies.css'
import './styles/forecast.css'
import './styles/products.css'
import './styles/users.css'
import './styles/publish.css'

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
