import { Routes, Route } from 'react-router-dom'
import './App.css'
import Home from './pages/Home/Home'
import MKPage from './pages/MKPage/MKPage'
import logo from './assets/logo.png' 
import UtterancePage from './pages/UtterancePage/UtterancePage'

function App() {
  return (
    <div className="app">
      <header className="app-header">

        <div className="logo-container">
        <img src={logo} alt="App Logo" className="app-logo" />
        
        </div>
<h1>חיפוש-כנסת</h1>
        
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
