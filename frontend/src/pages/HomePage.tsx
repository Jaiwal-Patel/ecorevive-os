import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  MapPinned,
  Recycle,
  ShieldCheck,
  Truck,
  Users,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'
import type { ImpactMetric, PublicConfig } from '../types'

function formatMetricValue(value: string) {
  const numeric = Number(value)

  if (Number.isNaN(numeric)) {
    return value
  }

  return numeric.toLocaleString()
}

export function HomePage() {
  const { data: config } = useQuery({
    queryKey: ['public-config'],
    queryFn: async () =>
      (await api.get<PublicConfig>('/public/config/')).data,
  })

  const { data: impact = [] } = useQuery({
    queryKey: ['public-impact'],
    queryFn: async () =>
      (await api.get<ImpactMetric[]>('/public/impact/')).data,
  })

  return (
    <PublicLayout>
      <header className="hero">
        <div className="hero-copy">
          <span className="eyebrow">
            <Recycle size={15} />
            Community-led circular action
          </span>

          <h1>
            Give unused electronics a responsible next chapter.
          </h1>

          <p>
            {config?.tagline || "Today's Actions. Tomorrow's Impact."}{' '}
            EcoRevive makes responsible collection easier for
            communities by connecting requests, volunteers and
            verified recycler handovers through one coordinated
            workflow.
          </p>

          <div className="hero-actions">
            <Link className="button" to="/register">
              Request a collection
              <ArrowRight size={18} />
            </Link>

            <Link
              className="button button-ghost"
              to="/how-it-works"
            >
              See how it works
            </Link>
          </div>

          <div className="trust-line">
            <ShieldCheck size={18} />
            <span>
              Address data stays private. Public reporting uses
              aggregated impact figures.
            </span>
          </div>
        </div>

        <div className="hero-card">
          <div className="map-grid">
            <span className="pulse p1" />
            <span className="pulse p2" />
            <span className="pulse p3" />
            <span className="pulse p4" />
            <MapPinned size={44} />
          </div>

          <div className="hero-card-body">
            <span>Service area</span>
            <strong>
              {config?.service_city || 'Dubai'}, UAE
            </strong>
            <small>
              Community collection and recycling coordination
            </small>
          </div>
        </div>
      </header>

      {impact.length > 0 && (
        <section className="impact-strip">
          {impact.slice(0, 4).map((metric) => (
            <div key={metric.id}>
              <strong>
                {formatMetricValue(metric.value)}
                {metric.unit && <sup> {metric.unit}</sup>}
              </strong>
              <span>{metric.label}</span>
            </div>
          ))}
        </section>
      )}

      <section className="section">
        <div className="section-heading">
          <span className="eyebrow">
            A simpler route to responsible recycling
          </span>

          <h2>
            From a resident's request to verified recycler
            handover.
          </h2>

          <p className="public-section-lead">
            EcoRevive removes the logistical friction that often
            leaves unused electronics sitting in homes.
          </p>
        </div>

        <div className="steps">
          <article>
            <span>01</span>
            <CheckCircle2 />
            <h3>Request</h3>
            <p>
              Tell us what you have and provide the collection
              details needed to coordinate a pickup.
            </p>
          </article>

          <article>
            <span>02</span>
            <Users />
            <h3>Coordinate</h3>
            <p>
              Requests are reviewed and organized so collections
              can be handled efficiently and responsibly.
            </p>
          </article>

          <article>
            <span>03</span>
            <Truck />
            <h3>Collect</h3>
            <p>
              Approved volunteers and EcoRevive operations move
              material from the community into the collection
              workflow.
            </p>
          </article>

          <article>
            <span>04</span>
            <Recycle />
            <h3>Verify</h3>
            <p>
              Collected material is aggregated and transferred
              into established recycling infrastructure.
            </p>
          </article>
        </div>

        <div className="public-inline-link">
          <Link to="/how-it-works">
            Explore the complete process
            <ArrowRight size={17} />
          </Link>
        </div>
      </section>

      <section className="section audience">
        <div>
          <span className="eyebrow">
            Built around community participation
          </span>

          <h2>
            One initiative. Different ways to contribute.
          </h2>

          <p>
            Residents make responsible disposal easier by
            participating. Volunteers help collections move.
            Organizations can consolidate larger volumes, while
            EcoRevive coordinates the process behind the scenes.
          </p>
        </div>

        <div className="audience-grid">
          <span>
            <Users />
            Residents
          </span>

          <span>
            <Building2 />
            Organizations
          </span>

          <span>
            <Truck />
            Volunteers
          </span>

          <span>
            <ShieldCheck />
            Verified workflow
          </span>
        </div>
      </section>

      <section className="public-discover section">
        <div className="section-heading">
          <span className="eyebrow">
            Explore EcoRevive
          </span>

          <h2>
            More than a pickup service.
          </h2>
        </div>

        <div className="public-discover-grid">
          <Link to="/about">
            <strong>Our story</strong>
            <p>
              Why EcoRevive began and how a community effort
              became a repeatable operation.
            </p>
            <span>
              About EcoRevive <ArrowRight size={16} />
            </span>
          </Link>

          <Link to="/how-it-works">
            <strong>The process</strong>
            <p>
              See what happens from the moment a request is
              submitted through recycler handover.
            </p>
            <span>
              How it works <ArrowRight size={16} />
            </span>
          </Link>

          <Link to="/impact">
            <strong>Measured impact</strong>
            <p>
              View the latest public figures and how recycling
              handovers are documented.
            </p>
            <span>
              View impact <ArrowRight size={16} />
            </span>
          </Link>
        </div>
      </section>

      <section className="cta">
        <div>
          <span className="eyebrow">
            Start with one responsible action
          </span>

          <h2>
            Have unused electronics ready for a better ending?
          </h2>
        </div>

        <Link className="button button-light" to="/register">
          Make an impact
          <ArrowRight size={18} />
        </Link>
      </section>
    </PublicLayout>
  )
}
