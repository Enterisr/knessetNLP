import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { resolveServerURI } from '../../utils'
import type { Utterance, MKMetadata } from '../../types'
import './MKPage.css'
import defaultMkImage from '../../assets/default-mk.svg'

const MKPage = () => {
  const { mkName, query } = useParams<{ mkName: string; query: string }>()
  const [utterances, setUtterances] = useState<Utterance[]>([])
  const [metadata, setMetadata] = useState<MKMetadata | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (mkName && query) {
      fetchMKUtterances(mkName, query)
    }
  }, [mkName, query])

  const fetchMKUtterances = async (mkName: string, query: string) => {
    setLoading(true)
    try {
      const response = await fetch(resolveServerURI(`/api/query?query=${encodeURIComponent(query)}`))
      const data = await response.json()
      
      if (data.response) {
        const decodedMkName = decodeURIComponent(mkName)
        
        // Search through the response to find the MK by name
        let found = false
        Object.entries(data.response).forEach(([, mkData]) => {
          if (mkData && typeof mkData === 'object' && 'name' in mkData && mkData.name === decodedMkName) {
            // We found the MK
            found = true
            
            // Get the utterances and metadata
            if ('utterances' in mkData && Array.isArray(mkData.utterances)) {
              setUtterances(mkData.utterances)
            } else {
              setUtterances([])
            }
            
            // Set metadata if available
            if ('metadata' in mkData && typeof mkData.metadata === 'object') {
              setMetadata(mkData.metadata as MKMetadata)
            } else {
              setMetadata(null)
            }
          }
        })
        
        if (!found) {
          console.error('MK not found in response')
          setUtterances([])
          setMetadata(null)
        }
      } else {
        console.error('Invalid response format:', data)
        setUtterances([])
        setMetadata(null)
      }
      
      console.log(`Fetched data for MK ${mkName} with query "${query}"`)
    } catch (error) {
      console.error('Error fetching MK data:', error)
      setUtterances([])
      setMetadata(null)
    } finally {
      setLoading(false)
    }
  }

  const highlightQuery = (text: string, query: string) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  }

  if (loading) {
    return (
      <main className="app-main">
        <div className="mk-page-loading">
          <div className="spinner"></div>
          <p>Loading data...</p>
        </div>
      </main>
    )
  }

  if (!mkName || utterances.length === 0) {
    return (
      <main className="app-main">
        <div className="mk-page-error">
          <p>No member of Knesset or utterances found</p>
          <Link to={`/search/${encodeURIComponent(query!)}`} className="back-link">
            Back to search
          </Link>
        </div>
      </main>
    )
  }

  const decodedMkName = decodeURIComponent(mkName!)
  const photoUrl = metadata?.PhotoURL || defaultMkImage
  const factionName = metadata?.FactionName || ''

  return (
    <main className="app-main">
      <div className="mk-page">
        <div className="mk-page-header">
          <Link to={`/search/${encodeURIComponent(query!)}`} className="back-button">
            ← Back to MK list
          </Link>
          <div className="mk-profile">
            <div className="mk-photo-container">
              <img 
                src={photoUrl} 
                alt={decodedMkName}
                className="mk-photo"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = defaultMkImage
                }}
              />
            </div>
            <div className="mk-details">
              <h1 className="mk-name">{decodedMkName}</h1>
              {factionName && <p className="mk-faction">{factionName}</p>}
              <div className="mk-stats">
                <div className="mk-stat">
                  <span className="mk-stat-label">Utterances:</span>
                  <span className="mk-stat-value">{utterances.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mk-utterances">
          <h2>Utterances about "{decodeURIComponent(query!)}"</h2>
          <ul className="utterances-list">
            {utterances.map((utterance, index) => (
              <li key={index} className="utterance-item">
                <div className="utterance-content">
                  <p 
                    className="utterance-text" 
                    dangerouslySetInnerHTML={{ 
                      __html: highlightQuery(utterance.text, decodeURIComponent(query!)) 
                    }} 
                  />
                  <div className="utterance-metadata">
                    {utterance.src && (
                      <a 
                        href={utterance.src} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="utterance-source"
                      >
                        Source document
                      </a>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}

export default MKPage
