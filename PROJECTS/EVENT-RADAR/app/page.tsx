import Radar from '@/components/Radar';
export default function Page(){return <Radar stagingNotice={process.env.NEXT_PUBLIC_STAGING_NOTICE||''}/>}
