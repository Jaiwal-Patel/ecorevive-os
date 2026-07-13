import { ArrowRight, CheckCircle2, Clock3, PackageOpen, Recycle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Loading } from '../components/Loading'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { CollectionRequest, ImpactMetric, Paginated } from '../types'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: requestPage, isLoading } = useQuery({ queryKey:['requests'], queryFn:async() => (await api.get<Paginated<CollectionRequest>>('/collection-requests/')).data })
  const { data: impact=[] } = useQuery({ queryKey:['public-impact'], queryFn:async() => (await api.get<ImpactMetric[]>('/public/impact/')).data })
  if (isLoading) return <Loading label="Loading your workspace…"/>
  const requests=requestPage?.results ?? []
  const completed=requests.filter(r=>r.status==='completed').length
  const active=requests.filter(r=>!['completed','cancelled'].includes(r.status)).length
  return <div className="workspace"><div className="page-head"><div><span className="eyebrow">{new Intl.DateTimeFormat('en-AE',{weekday:'long',month:'long',day:'numeric'}).format(new Date())}</span><h1>Welcome, {user?.full_name.split(' ')[0]}.</h1><p>Track collections, coordinate next actions and see EcoRevive’s growing impact.</p></div><Link className="button" to="/requests/new">New collection <ArrowRight size={18}/></Link></div>
    {user?.must_change_password && <div className="alert alert-warning"><strong>Security action required.</strong> This account is using a temporary password. Change it now in Account settings.</div>}
    <div className="stat-grid"><article><span>Active requests</span><strong>{active}</strong><Clock3/></article><article><span>Completed</span><strong>{completed}</strong><CheckCircle2/></article><article><span>Your total requests</span><strong>{requests.length}</strong><PackageOpen/></article><article><span>Community e-waste</span><strong>{impact.find(m=>m.key==='ewaste_kg')?.value ?? '—'} <small>kg</small></strong><Recycle/></article></div>
    <section className="panel"><div className="panel-head"><div><h2>Recent collection requests</h2><p>Your latest operational activity.</p></div><Link to="/requests">View all</Link></div>{requests.length===0?<div className="empty"><PackageOpen/><h3>No collection requests yet</h3><p>Record the electronics you would like EcoRevive to collect.</p><Link className="button button-small" to="/requests/new">Create request</Link></div>:<div className="table-wrap"><table><thead><tr><th>Reference</th><th>Area</th><th>Items</th><th>Status</th><th>Updated</th></tr></thead><tbody>{requests.slice(0,6).map(r=><tr key={r.id}><td><Link to={`/requests/${r.id}`}><strong>{r.public_reference}</strong></Link></td><td>{r.area}</td><td>{r.items.reduce((sum,item)=>sum+item.quantity,0)}</td><td><StatusBadge status={r.status}/></td><td>{new Intl.DateTimeFormat('en-AE',{dateStyle:'medium'}).format(new Date(r.updated_at))}</td></tr>)}</tbody></table></div>}</section>
  </div>
}
