import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { resolveServerURI } from '../../utils'
import type { DetailedUtterance, MKMetadata } from '../../types'
import './MKPage.css'
import defaultMkImage from '../../assets/default-mk.svg'

const MKPage = () => {
  const { mkName, query } = useParams<{ mkName: string; query: string }>()
  const [utterances, setUtterances] = useState<DetailedUtterance[]>([])
  const [metadata, setMetadata] = useState<MKMetadata | null>(null)
  const [sentiment, setSentiment] = useState<number | undefined>(undefined)
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
            
            // Set sentiment if available
            if ('sentiment' in mkData && typeof mkData.sentiment === 'number') {
              setSentiment(mkData.sentiment)
            } else {
              setSentiment(undefined)
            }
          }
        })
        
        if (!found) {
          console.error('MK not found in response')
          setUtterances([])
          setMetadata(null)
          setSentiment(undefined)
        }
      } else {
        console.error('Invalid response format:', data)
        setUtterances([])
        setMetadata(null)
        setSentiment(undefined)
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

  // Determine sentiment display
  const getSentimentInfo = (sentiment: number | undefined) => {
    if (sentiment === undefined) return { label: 'Neutral', className: 'sentiment-neutral' };
    
    if (sentiment >= 4) return { label: 'Very Positive', className: 'sentiment-very-positive' };
    if (sentiment >= 3.5) return { label: 'Positive', className: 'sentiment-positive' };
    if (sentiment >= 2.5) return { label: 'Neutral', className: 'sentiment-neutral' };
    if (sentiment >= 2) return { label: 'Negative', className: 'sentiment-negative' };
    return { label: 'Very Negative', className: 'sentiment-very-negative' };
  };

  const sentimentInfo = getSentimentInfo(sentiment);

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
                <div className="mk-stat">
                  <span className="mk-stat-label">Overall Sentiment:</span>
                  <span className={`mk-stat-sentiment ${sentimentInfo.className}`}>
                    {sentimentInfo.label}
                    {sentiment !== undefined && (
                      <span className="sentiment-score"> ({sentiment.toFixed(1)})</span>
                    )}
                  </span>
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
