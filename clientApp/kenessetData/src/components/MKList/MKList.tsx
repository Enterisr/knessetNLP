import './MKList.css'
import type { MK } from '../types'

interface MKListProps {
  mks: MK[]
  onMKSelect: (mk: MK) => void
  loading: boolean
}

const MKList = ({ mks, onMKSelect, loading }: MKListProps) => {
  if (loading) {
    return (
      <div className="mk-list-loading">
        <div className="spinner"></div>
        <p>
          Loading...
        </p>
      </div>
    )
  }

  if (mks.length === 0) {
    return (
      <div className="mk-list-empty">
        <p>No results found</p>
      </div>
    )
  }

  return (
    <ul className="mk-list">
      {mks.map((mk) => (
        <li key={mk.id} className="mk-list-item" onClick={() => onMKSelect(mk)}>
          <h3 className="mk-list-item-title">{mk.title}</h3>
          <p className="mk-list-item-description">{mk.description}</p>
        </li>
      ))}
    </ul>
  )
}

export default MKList