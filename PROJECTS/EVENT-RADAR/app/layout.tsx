import type {Metadata,Viewport} from 'next';
import Brand from '@/components/Brand';
import './globals.css';
export const metadata:Metadata={title:'Пинто: события рядом',description:'Концерты, театр, вечеринки и новые знакомства. Афиша Северной Италии и Швейцарии.',icons:{icon:'/icon.svg'}};
export const viewport:Viewport={width:'device-width',initialScale:1,themeColor:'#101211',colorScheme:'dark'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="ru"><body><a className="skip-link" href="#main-content">Перейти к содержимому</a>{children}<footer className="site-footer"><Brand/><p>Больше встреч. Больше впечатлений.</p><small>Даты, цены и наличие билетов могут измениться. Перед покупкой проверьте источник.</small><span className="footer-region">Северная Италия · Швейцария</span></footer></body></html>;}
