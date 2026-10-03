import {notFound} from 'next/navigation';import LayoutCheck from '@/components/LayoutCheck';export default function Page(){if(process.env.NODE_ENV!=='development')notFound();return <LayoutCheck/>;}
