import { Routes, Route } from 'react-router-dom'
import './App.css'
import Home from './pages/Home'
import MKPage from './pages/MKPage'
import UtterancePage from './pages/UtterancePage'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>חיפוש דברי כנסת</h1>
      </header>
      
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search/:query" element={<Home />} />
        <Route path="/mk/:mkId/:query" element={<MKPage />} />
        <Route path="/mk/:mkId/:query/utterance/:utteranceId" element={<UtterancePage />} />
      </Routes>
    </div>
  )
}

export default App
