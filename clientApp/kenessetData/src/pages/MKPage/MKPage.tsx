import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import type { MK, Utterance } from '../types'
import './MKPage.css'

const MKPage = () => {
  const { mkId, query } = useParams<{ mkId: string; query: string }>()
  const navigate = useNavigate()
  const [mk, setMk] = useState<MK | null>(null)
  const [utterances, setUtterances] = useState<Utterance[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (mkId && query) {
      fetchMKAndUtterances(mkId, query)
    }
  }, [mkId, query])

  const getSentimentColor = (polarity: number): string => {
    if (polarity > 0.1) return '#28a745' // Green for positive
    if (polarity < -0.1) return '#dc3545' // Red for negative
    return '#6c757d' // Gray for neutral
  }

  const getSentimentLabel = (polarity: number): string => {
    if (polarity > 0.1) return 'חיובי'
    if (polarity < -0.1) return 'שלילי'
    return 'נייטרלי'
  }

  const getSubjectivityLabel = (subjectivity: number): string => {
    if (subjectivity > 0.6) return 'סובייקטיבי'
    if (subjectivity < 0.3) return 'אובייקטיבי'
    return 'מעורב'
  }

  const fetchMKAndUtterances = async (mkId: string, query: string) => {
    setLoading(true)
    try {
      // TODO: Fetch actual MK data and utterances
      // For now, using mock data
      
      // Mock MK data with photos and sentiment
      const mockMK: MK = {
        id: mkId,
        name: mkId === '1' ? 'בנימין נתניהו' : mkId === '2' ? 'יאיר לפיד' : 'בצלאל סמוטריץ',
        factionName: mkId === '1' ? 'הליכוד' : mkId === '2' ? 'יש עתיד' : 'הציונות הדתית',
        utteranceCount: 15,
        photoUrl: `/images/mks/mk-${mkId}.svg`,
        sentiment: {
          polarity: mkId === '1' ? 0.15 : mkId === '2' ? -0.08 : 0.25,
          subjectivity: mkId === '1' ? 0.65 : mkId === '2' ? 0.45 : 0.78
        }
      }
      
      // Mock utterances data with sentiment
      const mockUtterances: Utterance[] = [
        {
          id: '1',
          text: `נושא החינוך הוא בראש סדר העדיפויות שלנו, ואנחנו פועלים לשיפור המערכת החינוכית. יש צורך בהשקעה רבה יותר במורים ובתשתיות. אנו מתחייבים להגדיל את התקציב לחינוך ולהבטיח שכל ילד יקבל חינוך איכותי. זה הבסיס לעתיד המדינה.`,
          date: '2023-10-15',
          committee: 'ועדת החינוך',
          mkId: mkId,
          mkName: mockMK.name,
          sentiment: { polarity: 0.3, subjectivity: 0.6 }
        },
        {
          id: '2',
          text: `יש צורך בהשקעה נוספת בתחום הבטחון והגנה על אזרחי ישראל. המצב הביטחוני מחייב אותנו לחזק את צה"ל ואת כוחות הביטחון. אנו פועלים להבטיח שתהיה לנו יכולת הרתעה מלאה מול כל איום.`,
          date: '2023-10-20',
          committee: 'ועדת החוץ והבטחון',
          mkId: mkId,
          mkName: mockMK.name,
          sentiment: { polarity: 0.1, subjectivity: 0.5 }
        },
        {
          id: '3',
          text: `הכלכלה הישראלית צריכה לגדול ולהתפתח. אנו פועלים לעודד יזמות והשקעות. יש להקל על העסקים הקטנים והבינוניים ולהוריד מסים. זה יביא לצמיחה כלכלית ולהגדלת התעסוקה בישראל.`,
          date: '2023-11-02',
          committee: 'ועדת הכלכלה',
          mkId: mkId,
          mkName: mockMK.name,
          sentiment: { polarity: 0.2, subjectivity: 0.4 }
        }
      ]
      
      setMk(mockMK)
      setUtterances(mockUtterances)
      
      console.log(`Fetched data for MK ${mkId} with query "${query}"`)
    } catch (error) {
      console.error('Error fetching MK data:', error)
    } finally {
      setLoading(false)
    }
  }

  const highlightQuery = (text: string, query: string) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  }

  const handleUtteranceClick = (utteranceId: string) => {
    navigate(`/mk/${mkId}/${encodeURIComponent(query!)}/utterance/${utteranceId}`)
  }

  if (loading) {
    return (
      <main className="app-main">
        <div className="mk-page-loading">
          <div className="spinner"></div>
          <p>טוען נתונים...</p>
        </div>
      </main>
    )
  }

  if (!mk) {
    return (
      <main className="app-main">
        <div className="mk-page-error">
          <p>לא נמצא חבר כנסת</p>
          <Link to={`/search/${encodeURIComponent(query!)}`} className="back-link">
            חזור לחיפוש
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="app-main">
      <div className="mk-page">
        <div className="mk-page-header">
          <Link to={`/search/${encodeURIComponent(query!)}`} className="back-button">
            ← חזור לרשימת חברי הכנסת
          </Link>
          <div className="mk-profile">
            <div className="mk-photo-container">
              <img 
                src={mk.photoUrl} 
                alt={mk.name}
                className="mk-photo"
                onError={(e) => {
                  e.currentTarget.src = '/images/mks/default-mk.svg'
                }}
              />
            </div>
            <div className="mk-info">
              <h2>{mk.name}</h2>
              <p className="mk-faction">{mk.factionName}</p>
              <p className="search-context">אמירות על "{decodeURIComponent(query!)}"</p>
            </div>
          </div>
          
          {mk.sentiment && (
            <div className="sentiment-section">
              <h3>ניתוח רגש</h3>
              <div className="sentiment-metrics">
                <div className="sentiment-metric">
                  <span className="metric-label">רגש כללי:</span>
                  <span 
                    className="metric-value"
                    style={{ color: getSentimentColor(mk.sentiment.polarity) }}
                  >
                    {getSentimentLabel(mk.sentiment.polarity)} ({(mk.sentiment.polarity * 100).toFixed(1)}%)
                  </span>
                  <div className="sentiment-bar">
                    <div 
                      className="sentiment-fill"
                      style={{ 
                        width: `${Math.abs(mk.sentiment.polarity) * 100}%`,
                        backgroundColor: getSentimentColor(mk.sentiment.polarity)
                      }}
                    ></div>
                  </div>
                </div>
                <div className="sentiment-metric">
                  <span className="metric-label">סובייקטיביות:</span>
                  <span className="metric-value">
                    {getSubjectivityLabel(mk.sentiment.subjectivity)} ({(mk.sentiment.subjectivity * 100).toFixed(1)}%)
                  </span>
                  <div className="sentiment-bar">
                    <div 
                      className="sentiment-fill subjectivity"
                      style={{ 
                        width: `${mk.sentiment.subjectivity * 100}%`,
                        backgroundColor: '#6c757d'
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="utterances-section">
          {utterances.length === 0 ? (
            <div className="no-utterances">
              <p>לא נמצאו אמירות עבור {mk.name} בנושא "{decodeURIComponent(query!)}"</p>
            </div>
          ) : (
            <div className="utterances-grid">
              {utterances.map((utterance) => (
                <div 
                  key={utterance.id} 
                  className="utterance-card"
                  onClick={() => handleUtteranceClick(utterance.id)}
                >
                  <div className="utterance-metadata">
                    <span className="utterance-date">{utterance.date}</span>
                    <span className="utterance-committee">{utterance.committee}</span>
                    {utterance.sentiment && (
                      <span 
                        className="utterance-sentiment"
                        style={{ color: getSentimentColor(utterance.sentiment.polarity) }}
                      >
                        {getSentimentLabel(utterance.sentiment.polarity)}
                      </span>
                    )}
                  </div>
                  <div 
                    className="utterance-text"
                    dangerouslySetInnerHTML={{
                      __html: highlightQuery(utterance.text, decodeURIComponent(query!))
                    }}
                  />
                  <div className="utterance-action">
                    <span className="view-full">לחץ לצפייה מלאה →</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

export default MKPage
