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
        const sentiment = mkData.sentiment;
        
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
                <div className={`mk-sentiment ${sentimentInfo.className}`}>
                  <span className="sentiment-label">Sentiment: {sentimentInfo.label}</span>
                  {sentiment !== undefined && (
                    <span className="sentiment-score">({sentiment.toFixed(2)})</span>
                  )}
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  )
}

export default MKList