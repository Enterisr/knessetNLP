import './UtteranceItem.css'
import type { Utterance } from '../../types'

interface UtteranceItemProps {
  utterance: Utterance
  showRelevanceScore?: boolean
  maxLength?: number
}

const UtteranceItem = ({ utterance, showRelevanceScore = true, maxLength = 150 }: UtteranceItemProps) => {
  return (
    <div className="utterance-preview">
      <div className="utterance-scores">
        {showRelevanceScore && utterance.relevance_score !== undefined && (
          <span className="relevance-score">Score: {utterance.relevance_score.toFixed(3)}</span>
        )}
        {(utterance.committee || utterance.subject) && (
          <div 
            className={`protocol-info ${utterance.src ? 'clickable' : ''}`}
            onClick={utterance.src ? () => window.open(utterance.src, '_blank', 'noopener,noreferrer') : undefined}
            title={utterance.src ? 'לחץ לפתיחת הפרוטוקול המלא' : undefined}
          >
            {utterance.src && <span className="document-icon">📄 </span>}
            {utterance.committee && ` | מתוך: ${utterance.committee}`}
            {utterance.subject && ` | נושא: ${utterance.subject}`}
            {utterance.src && <span className="external-link-icon"> ↗</span>}
          </div>
        )}
      </div>
      <p className="utterance-text">
        {utterance.text.length > maxLength 
          ? utterance.text.substring(0, maxLength) + '...' 
          : utterance.text}
      </p>
    </div>
  )
}

export default UtteranceItem