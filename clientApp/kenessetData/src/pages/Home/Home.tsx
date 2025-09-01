import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import SearchBar from '../../components/SearchBar'
import MKList from '../../components/MKList'
import { resolveServerURI } from '../../utils'
import type { MK } from '../../types'
import "./Home.css"

const Home = () => {
  const { query } = useParams<{ query?: string }>()
  const navigate = useNavigate()
  const [mks, setMks] = useState<MK[]>([])
  const [loading, setLoading] = useState(false)
  const [currentQuery, setCurrentQuery] = useState(query || '')

  useEffect(() => {
    if (query) {
      handleSearch(query)
    }
  }, [query])

  const handleSearch = useCallback(async (searchQuery: string) => {
    setLoading(true)
    setCurrentQuery(searchQuery)
    
    // Update URL without triggering a page reload
    if (searchQuery !== query) {
      navigate(`/search/${encodeURIComponent(searchQuery)}`, { replace: false })
    }

    try {
      const response = await fetch(resolveServerURI(`/api/query?query=${encodeURIComponent(searchQuery)}`))
      const data = await response.json()
      
      // TODO: Process the actual response from your backend
      console.log('API Response:', data)
      const mockMKs: MK[] = [
        { id: '1', name: 'בנימין נתניהו', factionName: 'הליכוד', utteranceCount: 15 },
        { id: '2', name: 'יאיר לפיד', factionName: 'יש עתיד', utteranceCount: 8 },
        { id: '3', name: 'בצלאל סמוטריץ', factionName: 'הציונות הדתית', utteranceCount: 12 },
      ]
      
      setMks(mockMKs)
    } catch (error) {
      console.error('Error searching:', error)
    } finally {
      setLoading(false)
    }
  }, [navigate, query])

  const handleMKSelect = (mk: MK) => {
    navigate(`/mk/${mk.id}/${encodeURIComponent(currentQuery)}`)
  }

  return (
    <main className="app-main">
      
      <SearchBar onSearch={handleSearch} loading={loading} initialValue={currentQuery} />
      <MKList 
        mks={mks} 
        onMKSelect={handleMKSelect}
        query={currentQuery}
        loading={loading}
      />
    </main>
  )
}

export default Home
