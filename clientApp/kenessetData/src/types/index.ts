export interface Sentiment {
  polarity: number  // Range: -1 (negative) to 1 (positive)
  subjectivity: number  // Range: 0 (objective) to 1 (subjective)
}

export interface Utterance {
  text: string
  mk: string
  src: string
}

export interface MKMetadata {
  Id?: number
  FirstName?: string
  LastName?: string
  Email?: string
  FactionName?: string
  FactionID?: number
  PhotoURL?: string
  SiteId?: number
  PhotoStatus?: string
  [key: string]: unknown // Allow for any additional properties
}

export interface MKData {
  utterances: Utterance[]
  metadata?: MKMetadata
}

export interface MKUtterances {
  [mk: string]: MKData
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
