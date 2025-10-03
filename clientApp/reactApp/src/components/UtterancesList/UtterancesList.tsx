import './UtterancesList.css'
import type { DetailedUtterance } from '../../types/index'

interface UtterancesListProps {
  utterances: DetailedUtterance[]
  query: string
  onBack: () => void
  loading: boolean
}

const UtterancesList = ({ utterances, query, onBack, loading }: UtterancesListProps) => {
  const highlightQuery = (text: string, query: string) => {
    if (!query) return text
    
    const regex = new RegExp(`(${query})`, 'gi')
    const newText=  text.replace(regex, '<mark>$1</mark>')
    return <div>{newText}</div>
  }

  return (
    <div className="utterances-list">
      <div className="utterances-header">
        <button onClick={onBack} className="back-button">
          Back
        </button>
        <h2 className="header-title">Utterances</h2>
      </div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div className="utterances-content">
          {utterances.length === 0 ? (
            <div className="no-utterances">No utterances found.</div>
          ) : (
            utterances.map((utterance) => (
              <div key={utterance.id} className="utterance-item">
                <div className="utterance-text">
                  {highlightQuery(utterance.text, query)}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default UtterancesList