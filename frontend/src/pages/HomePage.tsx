import { ArrowRight, Building2, CheckCircle2, MapPinned, Recycle, ShieldCheck, Truck, Users } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Logo } from '../components/Logo'
import type { ImpactMetric, PublicConfig } from '../types'

export function HomePage() {
  const { data: config } = useQuery({ queryKey: ['public-config'], queryFn: async () => (await api.get<PublicConfig>('/public/config/')).data })
  const { data: impact = [] } = useQuery({ queryKey: ['public-impact'], queryFn: async () => (await api.get<ImpactMetric[]>('/public/impact/')).data })

  return <div className="public-page">
    <nav className="public-nav"><Logo /><div><a href="#how">How it works</a><a href="#impact">Impact</a><a href={config?.public_site_url || '#'} target="_blank" rel="noreferrer">About EcoRevive</a><Link className="button button-small button-ghost" to="/login">Log in</Link></div></nav>
    <header className="hero">
      <div className="hero-copy"><span className="eyebrow"><Recycle size={15}/> Community-led circular action</span><h1>Give electronics a responsible next chapter.</h1><p>{config?.tagline || "Today's Actions. Tomorrow's Impact."} EcoRevive OS coordinates pickups, volunteers, certified recycler handovers and measurable community impact across Dubai.</p><div className="hero-actions"><Link className="button" to="/register">Request a collection <ArrowRight size={18}/></Link><a className="button button-ghost" href="#how">See how it works</a></div><div className="trust-line"><ShieldCheck size={18}/><span>Address data stays private. Public reports use aggregated statistics.</span></div></div>
      <div className="hero-card"><div className="map-grid"><span className="pulse p1"/><span className="pulse p2"/><span className="pulse p3"/><span className="pulse p4"/><MapPinned size={44}/></div><div className="hero-card-body"><span>Service area</span><strong>{config?.service_city || 'Dubai'}, UAE</strong><small>Household and corporate collection coordination</small></div></div>
    </header>
    <section id="impact" className="impact-strip">{impact.slice(0,4).map(metric => <div key={metric.id}><strong>{Number(metric.value).toLocaleString()}<sup>{metric.unit ? ` ${metric.unit}` : '+'}</sup></strong><span>{metric.label}</span></div>)}</section>
    <section id="how" className="section"><div className="section-heading"><span className="eyebrow">One traceable workflow</span><h2>From a resident’s request to certified recycling</h2></div><div className="steps">
      <article><span>01</span><CheckCircle2/><h3>Request</h3><p>Residents and organizations record devices, quantities, preferred timing and collection instructions.</p></article>
      <article><span>02</span><Users/><h3>Coordinate</h3><p>EcoRevive administrators review requests, cluster nearby pickups and assign approved volunteers.</p></article>
      <article><span>03</span><Truck/><h3>Collect</h3><p>Collections are tracked through scheduled, assigned and collected milestones with a complete audit history.</p></article>
      <article><span>04</span><Recycle/><h3>Verify</h3><p>Items are aggregated and transferred to a certified recycler, with receipts and verified weights recorded.</p></article>
    </div></section>
    <section className="section audience"><div><span className="eyebrow">Built for a community</span><h2>One platform, clear roles</h2><p>Households, corporate coordinators, volunteers and operations leaders each see the tools they need—without unnecessary access to private information.</p></div><div className="audience-grid"><span><Users/>Residents</span><span><Building2/>Organizations</span><span><Truck/>Volunteers</span><span><ShieldCheck/>Administrators</span></div></section>
    <section className="cta"><div><span className="eyebrow">Start with one responsible action</span><h2>Schedule your e-waste collection.</h2></div><Link className="button button-light" to="/register">Create an account <ArrowRight size={18}/></Link></section>
    <footer><Logo/><span>EcoRevive Dubai · {new Date().getFullYear()}</span><a href={config?.public_site_url || '#'} target="_blank" rel="noreferrer">Public initiative site</a></footer>
  </div>
}
