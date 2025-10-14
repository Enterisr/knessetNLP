export interface Utterance {
  text: string;
  mk: string;
  src: string;
  committee?: string;
  subject?: string;
  sentiment?: number; // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
  relevance_score?: number; // Relevance score for this query
}

export interface MKMetadata {
  Id?: number;
  FirstName?: string;
  LastName?: string;
  Email?: string;
  FactionName?: string;
  FactionID?: number;
  PhotoURL?: string;
  SiteId?: number;
  PhotoStatus?: string;
  sentiment?: number;
  [key: string]: unknown; // Allow for any additional properties
}

export interface MKData {
  utterances: Utterance[];
  metadata?: MKMetadata;
  name?: string;
  sentiment?: number; // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
  total_relevance_score?: number; // Total relevance score for this query
}

export interface MKUtterances {
  [mk: string]: MKData;
}

export interface DetailedUtterance {
  id: string;
  text: string;
  date: string;
  committee: string;
  src?: string;
  mkId?: string;
  mkName?: string;
  sentiment?: number; // Range: 1-5 (1=very negative/nasty, 5=very positive/angel)
}
