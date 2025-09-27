import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { resolveServerURI, getSentimentInfo } from '../../utils'
import type { Utterance, MKMetadata } from '../../types'
import UtteranceItem from '../../components/UtteranceItem/UtteranceItem'
import './MKPage.css'
import defaultMkImage from '../../assets/default-mk.svg'

const MKPage = () => {
  const { mkName, query } = useParams<{ mkName: string; query: string }>()
  const [utterances, setUtterances] = useState<Utterance[]>([])
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
      
      const decodedMkName = decodeURIComponent(mkName)
      const mkData = data.response[decodedMkName]
      
      setUtterances(mkData?.utterances || [])
      setMetadata(mkData?.metadata || null)
      setSentiment(mkData?.sentiment)
      
    } catch (error) {
      console.error('Error fetching MK data:', error)
      setUtterances([])
      setMetadata(null)
      setSentiment(undefined)
    } finally {
      setLoading(false)
    }
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
  const sentimentInfo = getSentimentInfo(sentiment);

  return (
    <main className="app-main">
      <div className="mk-page">
        <div className="mk-page-header">
          <Link to={`/search/${encodeURIComponent(query!)}`} className="back-button">
            ← חזרה לרשימת ח"כ
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
                  <span className="mk-stat-label">התבטאויות:</span>
                  <span className="mk-stat-value">{utterances.length}</span>
                </div>
                <div className="mk-stat">
                  <span className="mk-stat-label">דרך ארץ כללית:</span>
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
          <h2>התבטאויות על "{decodeURIComponent(query!)}"</h2>
          <div className="utterances-container">
            {utterances.map((utterance, index) => (
              <UtteranceItem 
                key={index} 
                utterance={utterance} 
                showRelevanceScore={true}
                maxLength={300}
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  )
}

export default MKPage
