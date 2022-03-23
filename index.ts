import axios from 'axios'
import * as HTMLParser from 'node-html-parser'
import { XMLParser } from 'fast-xml-parser'
import { ExploreTrendRequest, SearchProviders } from 'g-trends'

export interface MemeInfo {
    name: string
    types: string[]
    year: number
    origin: string
}

export const Test = async () => {
    const response = axios.get('https://www.youtube.com/feeds/videos.xml?channel_id=UCaHT88aobpcvRFEuy4v5Clg')

    const parser = new XMLParser()
    const entry = parser.parse(await (await response).data).feed.entry

    return entry.map(e => { return e.title.replace(/“|”/g, '"') })
}
