export interface MK {
  id: string
  name: string
  factionName: string
  utteranceCount: number
}

export interface Utterance {
  id: string
  text: string
  date: string
  committee: string
  mkId?: string
  mkName?: string
}
