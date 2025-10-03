import { useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import { resolveServerURI } from '../utils'
import type { MKUtterances } from '../types'
import { SearchContext, type SearchContextType } from './SearchContext.ts'

interface SearchProviderProps {
  children: ReactNode
}

export const SearchProvider = ({ children }: SearchProviderProps) => {
  const [searchResults, setSearchResults] = useState<MKUtterances>({})
  const [currentQuery, setCurrentQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults({})
      setCurrentQuery('')
      return
    }

    // If we already have results for this query, don't fetch again
    if (currentQuery === query && Object.keys(searchResults).length > 0) {
      return
    }

    setLoading(true)
    setError(null)
    setCurrentQuery(query)

    try {
      const response = await fetch(
        resolveServerURI(`/api/query?query=${encodeURIComponent(query)}`),
        {
          cache: 'force-cache',
          headers: {
            'Cache-Control': 'max-age=86400, immutable'
          }
        }
      )
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.response) {
        console.log('Backend response:', data.response)
        setSearchResults(data.response as MKUtterances)
      } else {
        console.error('Invalid response format:', data)
        setSearchResults({})
        setError('Invalid response format from server')
      }
    } catch (error) {
      console.error('Error searching:', error)
      setSearchResults({})
      setError(error instanceof Error ? error.message : 'An error occurred while searching')
    } finally {
      setLoading(false)
    }
  }, [currentQuery, searchResults])

  const clearResults = useCallback(() => {
    setSearchResults({})
    setCurrentQuery('')
    setError(null)
  }, [])

  const value: SearchContextType = {
    searchResults,
    currentQuery,
    loading,
    error,
    search,
    clearResults
  }

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  )
}