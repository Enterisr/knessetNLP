import './MKList.css'
import type { MK } from '../types'

interface MKListProps {
  mks: MK[]
  onMKSelect: (mk: MK) => void
  query: string
  loading: boolean
}

const MKList = ({ mks, onMKSelect, query, loading }: MKListProps) => {
  if (loading) {
    return (
      <div className="mk-list-loading">
        <div className="spinner"></div>
        <p>מחפש חברי כנסת רלוונטיים...</p>
      </div>
    )
  }

  if (mks.length === 0 && query) {
    return (
      <div className="mk-list-empty">
        <p>לא נמצאו חברי כנסת רלוונטיים לחיפוש "{query}"</p>
      </div>
    )
  }

  if (mks.length === 0) {
    return (
      <div className="mk-list-welcome">
        <p>הכנס מונח חיפוש למעלה כדי למצוא דברי חברי כנסת רלוונטיים</p>
      </div>
    )
  }

  return (
    <div className="mk-list">
      <h2>חברי כנסת שדיברו על "{query}" ({mks.length})</h2>
      <div className="mk-grid">
        {mks.map((mk) => (
          <div
            key={mk.id}
            className="mk-card"
            onClick={() => onMKSelect(mk)}
          >
            <div className="mk-name">{mk.name}</div>
            <div className="mk-faction">{mk.factionName}</div>
            <div className="mk-utterance-count">
              {mk.utteranceCount} אמירות רלוונטיות
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MKList
