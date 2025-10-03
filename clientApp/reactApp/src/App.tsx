import './App.css'
import { SearchProvider } from './contexts/SearchContext.tsx'
import AppRouter from './components/AppRouter/AppRouter'
import logo from './assets/logo.png' 

function App() {
  return (
    <SearchProvider>
      <div className="app">
        <header className="app-header">
          <div className="logo-container">
            <img src={logo} alt="App Logo" className="app-logo" />
          </div>
          <h1>חיפוש-כנסת</h1>
        </header>
        
        <AppRouter />
      </div>
    </SearchProvider>
  )
}

export default App
