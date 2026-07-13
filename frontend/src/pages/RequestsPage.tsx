import { Filter, Plus, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Loading } from '../components/Loading'
import { StatusBadge } from '../components/StatusBadge'
import type { CollectionRequest, Paginated } from '../types'

export function RequestsPage() {
  const [search,setSearch]=useState(''); const [status,setStatus]=useState('all')
  const {data,isLoading}=useQuery({queryKey:['requests'],queryFn:async()=>(await api.get<Paginated<CollectionRequest>>('/collection-requests/?page_size=100')).data})
  const requests=useMemo(()=> (data?.results??[]).filter(r=>(status==='all'||r.status===status)&&(`${r.public_reference} ${r.requester_name} ${r.area}`.toLowerCase().includes(search.toLowerCase()))),[data,search,status])
  if(isLoading)return <Loading/>
  return <div className="workspace"><div className="page-head"><div><span className="eyebrow">Operations ledger</span><h1>Collection requests</h1><p>Every request, status transition and collection item in one traceable view.</p></div><Link className="button" to="/requests/new"><Plus size={18}/>New request</Link></div><section className="panel"><div className="filters"><label className="search"><Search size={18}/><input placeholder="Search reference, resident or area" value={search} onChange={e=>setSearch(e.target.value)}/></label><label className="select-control"><Filter size={18}/><select value={status} onChange={e=>setStatus(e.target.value)}><option value="all">All statuses</option>{['draft','submitted','under_review','approved','scheduled','assigned','collected','handed_to_recycler','completed','cancelled'].map(s=><option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label></div><div className="table-wrap"><table><thead><tr><th>Reference</th><th>Requester</th><th>Location</th><th>Preferred date</th><th>Items</th><th>Status</th></tr></thead><tbody>{requests.map(r=><tr key={r.id}><td><Link to={`/requests/${r.id}`}><strong>{r.public_reference}</strong></Link></td><td>{r.requester_name}</td><td>{r.area}, {r.city}</td><td>{r.preferred_date??'Flexible'}</td><td>{r.items.reduce((sum,i)=>sum+i.quantity,0)}</td><td><StatusBadge status={r.status}/></td></tr>)}</tbody></table>{requests.length===0&&<div className="empty compact"><h3>No matching requests</h3><p>Try another filter or create a collection request.</p></div>}</div></section></div>
}
