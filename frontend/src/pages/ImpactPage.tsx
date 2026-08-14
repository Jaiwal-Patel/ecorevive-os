import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  FileCheck2,
  HeartHandshake,
  Recycle,
  Scale,
  ShieldCheck,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import { PublicLayout } from '../components/PublicLayout'
import type { ImpactMetric } from '../types'

function formatMetricValue(value: string) {
  const numeric = Number(value)

  if (Number.isNaN(numeric)) {
    return value
  }

  return numeric.toLocaleString()
}


function metricValueInKg(
  metric: ImpactMetric | undefined,
) {
  if (!metric) {
    return null
  }

  const numeric = Number(
    metric.value.replace(/,/g, ''),
  )

  if (Number.isNaN(numeric)) {
    return null
  }

  const unit = metric.unit
    .trim()
    .toLowerCase()

  if (
    unit === 'kg'
    || unit === 'kilogram'
    || unit === 'kilograms'
  ) {
    return numeric
  }

  if (
    unit === 't'
    || unit === 'tonne'
    || unit === 'tonnes'
    || unit === 'metric ton'
    || unit === 'metric tons'
    || unit === 'metric tonne'
    || unit === 'metric tonnes'
  ) {
    return numeric * 1000
  }

  return null
}

export function ImpactPage() {
  const {
    data: impact = [],
    isLoading,
  } = useQuery({
    queryKey: ['public-impact'],
    queryFn: async () =>
      (await api.get<ImpactMetric[]>('/public/impact/')).data,
  })

  const metrics = [...impact].sort(
    (left, right) =>
      left.display_order - right.display_order,
  )


  const electronicWasteMetric = metrics.find(
    (metric) =>
      metric.label
        .toLowerCase()
        .includes('electronic waste'),
  )

  const electronicWasteKg = metricValueInKg(
    electronicWasteMetric,
  )

  /*
   * EPA WARM's mixed-electronics recycling factor is
   * approximately 0.81 metric tonnes CO2e reduction per
   * short ton of electronics recycled.
   *
   * This is an illustrative model-based estimate, not an
   * audited carbon footprint, carbon credit or offset.
   */
  const estimatedCo2eTonnes =
    electronicWasteKg === null
      ? null
      : (
          electronicWasteKg
          / 907.18474
        ) * 0.81

  return (
    <PublicLayout>
      <section className="public-inner-hero">
        <div className="public-inner-hero-copy">
          <span className="eyebrow">
            <BarChart3 size={15} />
            EcoRevive impact
          </span>

          <h1>
            Community action becomes meaningful when it is
            measured.
          </h1>

          <p>
            EcoRevive tracks public impact separately from
            private collection information, allowing the
            community to see what collective participation is
            accomplishing.
          </p>
        </div>

        <aside className="public-hero-principle">
          <span>Our approach</span>

          <strong>
            Measure the outcome, not just the activity.
          </strong>

          <p>
            Collections matter because material ultimately
            reaches responsible recycling infrastructure.
            Handover records help connect activity to outcome.
          </p>
        </aside>
      </section>

      <section className="public-impact-section">
        <div className="section-heading">
          <span className="eyebrow">
            Live public metrics
          </span>

          <h2>
            EcoRevive's latest recorded impact.
          </h2>

          <p className="public-section-lead">
            These figures are loaded directly from EcoRevive OS
            rather than being maintained separately on this
            webpage.
          </p>
        </div>

        {isLoading ? (
          <div className="public-impact-empty">
            Loading impact metrics…
          </div>
        ) : metrics.length > 0 ? (
          <div className="public-metric-grid">
            {metrics.map((metric) => (
              <article key={metric.id}>
                <span>{metric.label}</span>

                <strong>
                  {formatMetricValue(metric.value)}
                </strong>

                {metric.unit && (
                  <small>{metric.unit}</small>
                )}

                {metric.description && (
                  <p>{metric.description}</p>
                )}
              </article>
            ))}


            <article className="impact-context-card">
              <span>
                Estimated recycling GHG benefit
              </span>

              <strong>
                {estimatedCo2eTonnes === null
                  ? '—'
                  : `≈${estimatedCo2eTonnes.toFixed(1)}`}
              </strong>

              <small>t CO₂e</small>

              <p>
                Model-based estimate from recorded electronic
                waste using the U.S. EPA WARM mixed-electronics
                recycling factor.
              </p>

              <em>ESTIMATE</em>
            </article>

            <article className="impact-context-card">
              <span>
                Downstream e-waste capacity
              </span>

              <strong>39,000</strong>

              <small>tonnes / year</small>

              <p>
                Published electronic-waste processing capacity
                of Enviroserve's Dubai Recycling Hub.
              </p>

              <em>PARTNER CONTEXT</em>
            </article>

            <article className="impact-context-card">
              <span>
                Partner facility recovery rate
              </span>

              <strong>96</strong>

              <small>%</small>

              <p>
                Material recovery rate reported for
                Enviroserve's mechanical separation process.
              </p>

              <em>PARTNER CONTEXT</em>
            </article>
          </div>
        ) : (
          <div className="public-impact-empty">
            Public impact metrics are being updated.
          </div>
        )}

        {!isLoading && metrics.length > 0 && (
          <div className="public-impact-methodology">
            <strong>About the additional context metrics</strong>

            <p>
              EcoRevive's recorded collection figures come
              directly from EcoRevive OS. The CO₂e figure is an
              illustrative recycling estimate based on the U.S.
              EPA WARM mixed-electronics factor. Facility
              capacity and recovery-rate figures describe
              Enviroserve's Recycling Hub and are not claimed as
              EcoRevive's own operating capacity.
            </p>

            <div className="public-source-links public-impact-source-links">
              <a
                href="https://www.epa.gov/electronics-batteries-management/assessment-tools-electronics-stewardship"
                target="_blank"
                rel="noreferrer"
              >
                EPA electronics methodology
                <ArrowRight size={15} />
              </a>

              <a
                href="https://dubaiindustrialcity.ae/media/press-release/enviroserve-launches-world-largest-integrated-e-waste-and-specialised-recycling-plant"
                target="_blank"
                rel="noreferrer"
              >
                Enviroserve facility source
                <ArrowRight size={15} />
              </a>
            </div>
          </div>
        )}
      </section>

      <section className="section public-split">
        <div className="public-copy-block">
          <span className="eyebrow">
            Verification
          </span>

          <h2>
            What happens after material is collected?
          </h2>

          <p>
            EcoRevive consolidates collected material and
            transfers it through recycler handovers rather than
            treating pickup itself as the final environmental
            outcome.
          </p>

          <p>
            EcoRevive works with Enviroserve UAE for recycler
            handovers. Goods receipts documenting transferred
            weights provide an evidence trail that can support
            verified impact reporting.
          </p>
        </div>

        <div className="public-proof-card">
          <FileCheck2 size={34} />

          <span>Documented handover</span>

          <strong>
            Weight, recycler and receipt information can be
            recorded together.
          </strong>

          <p>
            EcoRevive OS includes a handover workflow so impact
            reporting can be tied back to operational records.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <span className="eyebrow">
            What impact means to us
          </span>

          <h2>
            More than a kilogram counter.
          </h2>
        </div>

        <div className="public-story-cards">
          <article>
            <span>01</span>
            <Scale />
            <h3>Material diverted</h3>
            <p>
              Every responsible handover represents material
              redirected away from inappropriate disposal and
              toward recycling systems.
            </p>
          </article>

          <article>
            <span>02</span>
            <HeartHandshake />
            <h3>Community participation</h3>
            <p>
              Families, volunteers and organizations turn
              individual actions into a larger community
              outcome.
            </p>
          </article>

          <article>
            <span>03</span>
            <ShieldCheck />
            <h3>Accountability</h3>
            <p>
              Recorded workflows and handover evidence make
              impact claims stronger than estimates alone.
            </p>
          </article>
        </div>
      </section>

      <section className="section public-impact-principles">
        <div>
          <BadgeCheck />
          <strong>Measured</strong>
          <span>
            Public figures come from the EcoRevive impact
            system.
          </span>
        </div>

        <div>
          <Recycle />
          <strong>Responsible</strong>
          <span>
            The goal is recycler handover, not simply removal
            from a home.
          </span>
        </div>

        <div>
          <FileCheck2 />
          <strong>Documented</strong>
          <span>
            Handover records strengthen confidence in reported
            outcomes.
          </span>
        </div>
      </section>

      <section className="cta">
        <div>
          <span className="eyebrow">
            Add your action to the total
          </span>

          <h2>
            The next contribution can start with one collection.
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
