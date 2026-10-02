import type {Metadata} from 'next';import './globals.css';
export const metadata:Metadata={title:'Event Radar — события рядом',description:'Концерты, встречи, театр и networking в Северной Италии и Швейцарии.',icons:{icon:'/icon.svg'}};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="ru"><body>{children}<footer><span>EVENT RADAR</span><p>Дата и наличие билетов могут измениться. Перед покупкой проверьте страницу организатора.</p></footer></body></html>}
