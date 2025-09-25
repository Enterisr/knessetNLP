export interface Utterance {
  text: string
  mk: string
  src: string
  sentiment?: number  // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
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
  sentiment?: number  // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
}

export interface MKUtterances {
  [mk: string]: MKData
}

export interface DetailedUtterance {
  id: string
  text: string
  date: string
  committee: string
  src?: string
  mkId?: string
  mkName?: string
  sentiment?: number  // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
}
