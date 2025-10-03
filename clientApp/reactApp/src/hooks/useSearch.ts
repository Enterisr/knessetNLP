import { useContext } from 'react'
import { SearchContext, type SearchContextType } from '../contexts/SearchContext.ts'

export const useSearch = (): SearchContextType => {
  const context = useContext(SearchContext)
  if (!context) {
    throw new Error('useSearch must be used within a SearchProvider')
  }
  return context
}