import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { MK, Utterance } from '../types'
import './UtterancePage.css'

const UtterancePage = () => {
  const { mkId, query, utteranceId } = useParams<{ 
    mkId: string; 
    query: string; 
    utteranceId: string 
  }>()
  
  const [mk, setMk] = useState<MK | null>(null)
  const [utterance, setUtterance] = useState<Utterance | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (mkId && query && utteranceId) {
      fetchUtterance(mkId, utteranceId)
    }
  }, [mkId, query, utteranceId])

  const fetchUtterance = async (mkId: string, utteranceId: string) => {
    setLoading(true)
    try {
      // TODO: Fetch actual utterance data from backend
      // For now, using mock data
      
      const mockMK: MK = {
        id: mkId,
        name: mkId === '1' ? 'בנימין נתניהו' : mkId === '2' ? 'יאיר לפיד' : 'בצלאל סמוטריץ',
        factionName: mkId === '1' ? 'הליכוד' : mkId === '2' ? 'יש עתיד' : 'הציונות הדתית',
        utteranceCount: 15
      }

      const mockUtterances: { [key: string]: Utterance } = {
        '1': {
          id: '1',
          text: `נושא החינוך הוא בראש סדר העדיפויות שלנו, ואנחנו פועלים לשיפור המערכת החינוכית בכל הרמות.
          
          יש צורך בהשקעה רבה יותר במורים ובתשתיות החינוכיות. המצב הנוכחי מחייב אותנו לפעול במהירות ובנחישות. אנו מתחייבים להגדיל את התקציב לחינוך ולהבטיח שכל ילד בישראל יקבל חינוך איכותי ושוויוני.
          
          זה לא רק עניין של השקעה כספית, אלא גם של חזון חינוכי ברור. אנחנו צריכים לחנך דור שיוכל להתמודד עם האתגרים של המאה ה-21. זה הבסיס לעתיד החזק והמשגשג של מדינת ישראל.
          
          אני קורא לכל חברי הכנסת לתמוך ברפורמה החינוכית החשובה הזו. זה מעל ומעבר לפוליטיקה - זה עתידם של הילדים שלנו.`,
          date: '2023-10-15',
          committee: 'ועדת החינוך',
          mkId: mkId,
          mkName: mockMK.name
        },
        '2': {
          id: '2',
          text: `יש צורך בהשקעה נוספת בתחום הבטחון והגנה על אזרחי ישראל. המצב הביטחוני הנוכחי מחייב אותנו לחזק את צה"ל ואת כוחות הביטחון הפנימי.
          
          אנו פועלים להבטיח שתהיה לנו יכולת הרתעה מלאה מול כל איום, קרוב או רחוק. זה כולל השקעה בטכנולוגיות מתקדמות, הכשרת כוחות מקצועיים, וחיזוק הביטחון בכל המישורים.
          
          הביטחון הוא התנאי הבסיסי לקיום חיים נורמליים במדינה שלנו. בלי ביטחון, אין כלכלה, אין חברה, ואין עתיד. לכן, אנחנו חייבים להמשיך להיות הכח הביטחוני המוביל באזור.
          
          זה לא רק עניין של תקציבים, אלא של אסטרטגיה ביטחונית ארוכת טווח. אנחנו חייבים להיות מוכנים לכל תרחיש.`,
          date: '2023-10-20',
          committee: 'ועדת החוץ והבטחון',
          mkId: mkId,
          mkName: mockMK.name
        },
        '3': {
          id: '3',
          text: `הכלכלה הישראלית צריכה לגדול ולהתפתח בקצב מהיר יותר. אנו פועלים לעודד יזמות והשקעות, תוך הקלה על העסקים הקטנים והבינוניים.
          
          יש להוריד מסים ולצמצם ביורוקרטיה מיותרת. זה יביא לצמיחה כלכלית משמעותית ולהגדלת התעסוקה בכל רחבי ישראל. העסקים הם המנוע הכלכלי של המדינה.
          
          אנחנו גם צריכים לפתח תחומים חדשים כמו הייטק, אנרגיות מתחדשות, וביוטכנולוגיה. ישראל יכולה להיות מדינת סטארט-אפ מובילה בעולם, אבל זה דורש מדיניות כלכלית נכונה.
          
          החזון שלנו הוא כלכלה חזקה ויציבה שתאפשר לכל אזרח ישראלי לחיות בכבוד ובביטחון כלכלי. זה מתחיל בפתיחת השוק ובעידוד התחרותיות.`,
          date: '2023-11-02',
          committee: 'ועדת הכלכלה',
          mkId: mkId,
          mkName: mockMK.name
        }
      }
      
      setMk(mockMK)
      setUtterance(mockUtterances[utteranceId] || null)
    } catch (error) {
      console.error('Error fetching utterance:', error)
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
        <div className="utterance-page-loading">
          <div className="spinner"></div>
          <p>טוען אמירה...</p>
        </div>
      </main>
    )
  }

  if (!utterance || !mk) {
    return (
      <main className="app-main">
        <div className="utterance-page-error">
          <p>לא נמצאה אמירה</p>
          <Link to={`/mk/${mkId}/${encodeURIComponent(query!)}`} className="back-link">
            חזור לרשימת האמירות
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="app-main">
      <div className="utterance-page">
        <div className="utterance-page-header">
          <div className="breadcrumbs">
            <Link to={`/search/${encodeURIComponent(query!)}`} className="breadcrumb-link">
              תוצאות חיפוש
            </Link>
            <span className="breadcrumb-separator">›</span>
            <Link to={`/mk/${mkId}/${encodeURIComponent(query!)}`} className="breadcrumb-link">
              {mk.name}
            </Link>
            <span className="breadcrumb-separator">›</span>
            <span className="breadcrumb-current">אמירה</span>
          </div>
          
          <div className="utterance-info">
            <h1>אמירה של {mk.name}</h1>
            <div className="utterance-metadata">
              <div className="metadata-item">
                <strong>תאריך:</strong> {utterance.date}
              </div>
              <div className="metadata-item">
                <strong>ועדה:</strong> {utterance.committee}
              </div>
              <div className="metadata-item">
                <strong>סיעה:</strong> {mk.factionName}
              </div>
              <div className="metadata-item">
                <strong>נושא החיפוש:</strong> "{decodeURIComponent(query!)}"
              </div>
            </div>
          </div>
        </div>

        <div className="utterance-content">
          <div className="utterance-text-full">
            <h3>תוכן האמירה:</h3>
            <div 
              className="utterance-text-content"
              dangerouslySetInnerHTML={{
                __html: highlightQuery(utterance.text, decodeURIComponent(query!))
              }}
            />
          </div>
        </div>

        <div className="utterance-actions">
          <Link to={`/mk/${mkId}/${encodeURIComponent(query!)}`} className="back-button">
            ← חזור לכל האמירות של {mk.name}
          </Link>
        </div>
      </div>
    </main>
  )
}

export default UtterancePage
