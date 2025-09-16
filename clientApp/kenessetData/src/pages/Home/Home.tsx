import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import SearchBar from '../../components/SearchBar/SearchBar'
import MKList from '../../components/MKList/MKList'
import { resolveServerURI } from '../../utils'
import type { MKUtterances } from '../../types'
import "./Home.css"

const Home = () => {
  const { query } = useParams<{ query?: string }>()
  const navigate = useNavigate()
  const [mks, setMks] = useState<MKUtterances>({})
  const [loading, setLoading] = useState(false)
  const [currentQuery, setCurrentQuery] = useState(query || '')

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
      
      // Transform the response into the format expected by the MKList component
      const transformedData: MKUtterances = {}
      
      if (data.response) {
        // Process each MK entry in the response
        Object.entries(data.response).forEach(([, mkData]) => {
          if (mkData && typeof mkData === 'object' && 'name' in mkData && 'utterances' in mkData) {
            const mkName = mkData.name as string
            // Use the MK name as the key and store their utterances and metadata
            transformedData[mkName] = {
              utterances: Array.isArray(mkData.utterances) ? mkData.utterances : [],
              metadata: 'metadata' in mkData ? mkData.metadata as Record<string, unknown> : {}
            }
          }
        })
        
        console.log('Processed data:', transformedData)
        setMks(transformedData)
      } else {
        console.error('Invalid response format:', data)
        setMks({})
      }
    } catch (error) {
      console.error('Error searching:', error)
      setMks({})
    } finally {
      setLoading(false)
    }
  }, [navigate, query])

  useEffect(() => {
    if (query) {
      handleSearch(query)
    }
  }, [query, handleSearch])

  const handleMKSelect = (mkName: string) => {
    // Navigate to the MK page with the selected MK name and current query
    navigate(`/mk/${encodeURIComponent(mkName)}/${encodeURIComponent(currentQuery)}`)
  }

  return (
    <main className="app-main">
      <SearchBar onSearch={handleSearch} initialValue={currentQuery} />
      <MKList 
        mks={mks} 
        onMKSelect={handleMKSelect}
        loading={loading}
      />
    </main>
  )
}

export default Home
