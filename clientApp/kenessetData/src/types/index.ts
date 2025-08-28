export interface Sentiment {
  polarity: number  // Range: -1 (negative) to 1 (positive)
  subjectivity: number  // Range: 0 (objective) to 1 (subjective)
}

export interface MK {
  id: string
  name: string
  factionName: string
  utteranceCount: number
  photoUrl?: string
  sentiment?: Sentiment
}

export interface Utterance {
  id: string
  text: string
  date: string
  committee: string
  mkId?: string
  mkName?: string
  sentiment?: Sentiment
}
