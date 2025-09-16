import './MKList.css'
import type { MKUtterances } from '../../types'
import defaultMkImage from '../../assets/default-mk.svg'

interface MKListProps {
  mks: MKUtterances
  onMKSelect: (mkName: string) => void
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

  const mkNames = Object.keys(mks)

  if (mkNames.length === 0) {
    return (
      <div className="mk-list-empty">
        <p>No results found</p>
      </div>
    )
  }

  return (
    <ul className="mk-list">
      {mkNames.map((mkName) => {
        const mkData = mks[mkName];
        const photoUrl = mkData.metadata?.PhotoURL || defaultMkImage;
        const party = mkData.metadata?.FactionName || '';
        
        return (
          <li key={mkName} className="mk-list-item" onClick={() => onMKSelect(mkName)}>
            <div className="mk-list-item-content">
              <div className="mk-photo-container">
                <img 
                  src={photoUrl} 
                  alt={`${mkName}`} 
                  className="mk-photo" 
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = defaultMkImage;
                  }}
                />
              </div>
              <div className="mk-details">
                <h3 className="mk-list-item-title">{mkName}</h3>
                {party && <p className="mk-list-item-party">{party}</p>}
                <p className="mk-list-item-description">{mkData.utterances.length} utterances</p>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  )
}

export default MKList