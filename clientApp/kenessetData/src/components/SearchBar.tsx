import { useState, useEffect } from 'react'
import './SearchBar.css'

interface SearchBarProps {
  onSearch: (query: string) => void
  loading: boolean
  initialValue?: string
}

const SearchBar = ({ onSearch, loading, initialValue = '' }: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue)

  useEffect(() => {
    setQuery(initialValue)
  }, [initialValue])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="search-input-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="חפש בדברי חברי הכנסת..."
          className="search-input"
          disabled={loading}
        />
        <button 
          type="submit" 
          className="search-button"
          disabled={loading || !query.trim()}
        >
          {loading ? 'מחפש...' : 'חפש'}
        </button>
      </div>
    </form>
  )
}

export default SearchBar
