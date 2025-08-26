import './UtterancesList.css'
import type { MK, Utterance } from '../types'

interface UtterancesListProps {
  mk: MK
  utterances: Utterance[]
  query: string
  onBack: () => void
  loading: boolean
}

const UtterancesList = ({ mk, utterances, query, onBack, loading }: UtterancesListProps) => {
  const highlightQuery = (text: string, query: string) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  }

  return (
    <div className="utterances-list">
      <div className="utterances-header">
        <button onClick={onBack} className="back-button">
          ← חזור לרשימת חברי הכנסת
        </button>
        <div className="mk-info">
          <h2>{mk.name}</h2>
          <p className="mk-faction">{mk.factionName}</p>
          <p className="search-context">אמירות על "{query}"</p>
        </div>
      </div>

      {loading ? (
        <div className="utterances-loading">
          <div className="spinner"></div>
          <p>טוען אמירות...</p>
        </div>
      ) : (
        <div className="utterances-content">
          {utterances.length === 0 ? (
            <div className="no-utterances">
              <p>לא נמצאו אמירות עבור {mk.name} בנושא "{query}"</p>
            </div>
          ) : (
            <div className="utterances-grid">
              {utterances.map((utterance) => (
                <div key={utterance.id} className="utterance-card">
                  <div className="utterance-metadata">
                    <span className="utterance-date">{utterance.date}</span>
                    <span className="utterance-committee">{utterance.committee}</span>
                  </div>
                  <div 
                    className="utterance-text"
                    dangerouslySetInnerHTML={{
                      __html: highlightQuery(utterance.text, query)
                    }}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default UtterancesList
