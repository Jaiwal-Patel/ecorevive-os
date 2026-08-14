import {
  ArrowRight,
  BadgeCheck,
  HeartHandshake,
  Recycle,
  ShieldCheck,
  Sparkles,
  UserRound,
  Workflow,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { PublicLayout } from '../components/PublicLayout'

export function AboutPage() {
  return (
    <PublicLayout>
      <section className="public-inner-hero">
        <div className="public-inner-hero-copy">
          <span className="eyebrow">
            <HeartHandshake size={15} />
            About EcoRevive Dubai
          </span>

          <h1>
            Making responsible recycling easier to act on.
          </h1>

          <p>
            EcoRevive Dubai is a community-led initiative built
            around a simple idea: people are far more likely to
            recycle responsibly when the process is convenient,
            trustworthy and close to home.
          </p>
        </div>

        <aside className="public-hero-principle">
          <span>Why EcoRevive exists</span>

          <strong>
            Good intentions should not be defeated by difficult
            logistics.
          </strong>

          <p>
            EcoRevive bridges the gap between households ready
            to recycle and the systems capable of processing
            material responsibly.
          </p>
        </aside>
      </section>

      <section className="section">
        <div className="section-heading">
          <span className="eyebrow">
            How it began
          </span>

          <h2>
            The missing piece was accessibility.
          </h2>

          <p className="public-section-lead">
            Community interactions revealed a recurring pattern:
            homes contained old laptops, chargers, phones,
            cables, routers and other unused electronics, but
            disposing of them responsibly was often inconvenient.
          </p>
        </div>

        <div className="public-story-cards">
          <article>
            <span>01</span>
            <Sparkles />
            <h3>Notice the gap</h3>
            <p>
              Households wanted to recycle, yet many devices
              remained stored for months or years because there
              was no simple collection route.
            </p>
          </article>

          <article>
            <span>02</span>
            <Recycle />
            <h3>Bring recycling closer</h3>
            <p>
              EcoRevive began coordinating community collections
              so residents did not have to navigate disposal
              channels alone.
            </p>
          </article>

          <article>
            <span>03</span>
            <Workflow />
            <h3>Build a repeatable system</h3>
            <p>
              As participation grew, the workflow evolved from
              manual coordination into a structured digital
              platform: EcoRevive OS.
            </p>
          </article>
        </div>
      </section>

      <section className="section audience public-mission-section">
        <div>
          <span className="eyebrow">
            Our mission
          </span>

          <h2>
            Make responsible action easier to repeat.
          </h2>

          <p>
            EcoRevive exists to lower the practical barriers to
            recycling by coordinating collection, aggregation
            and responsible recycler handover in one community
            workflow.
          </p>
        </div>

        <div className="public-mission-points">
          <div>
            <HeartHandshake />
            <span>
              <strong>Community-led</strong>
              Participation starts with residents choosing to act.
            </span>
          </div>

          <div>
            <ShieldCheck />
            <span>
              <strong>Accountable</strong>
              Collections move through a traceable operational
              process.
            </span>
          </div>

          <div>
            <Recycle />
            <span>
              <strong>Responsible</strong>
              Material is directed into established recycling
              infrastructure.
            </span>
          </div>
        </div>
      </section>

      <section className="section public-split">
        <div className="public-copy-block">
          <span className="eyebrow">
            Responsible recycling
          </span>

          <h2>
            Collection is only the beginning.
          </h2>

          <p>
            EcoRevive's responsibility does not stop when
            material leaves a resident's home. Collected
            material is consolidated for transfer into
            professional recycling infrastructure.
          </p>

          <p>
            EcoRevive works with Enviroserve UAE for recycler
            handovers. Official goods receipts provide
            documentary evidence of transferred weight and help
            support accountable impact reporting.
          </p>

          <Link className="public-text-link" to="/impact">
            See how impact is measured
            <ArrowRight size={17} />
          </Link>
        </div>

        <div className="public-proof-card">
          <BadgeCheck size={34} />

          <span>Accountability chain</span>

          <strong>
            Collection → aggregation → recycler handover →
            recorded impact
          </strong>

          <p>
            A community claim becomes more meaningful when the
            final handover can be documented.
          </p>
        </div>
      </section>

      <section className="section public-founder-section">
        <div className="public-founder-card">
          <div className="public-founder-icon">
            <UserRound size={30} />
          </div>

          <div>
            <span className="eyebrow">
              Founder
            </span>

            <h2>Founded by Jaiwal Patel</h2>

            <p>
              EcoRevive Dubai began as a student-led effort to
              make responsible recycling easier within local
              communities. What started with individual
              collections developed into a repeatable community
              operation.
            </p>

            <p>
              As the manual workflow grew more difficult to
              coordinate, Jaiwal developed EcoRevive OS to
              digitize requests, volunteer coordination,
              collection progress and recycler handovers.
            </p>
          </div>
        </div>
      </section>

      <section className="section public-platform-section">
        <div>
          <span className="eyebrow">
            From initiative to infrastructure
          </span>

          <h2>
            EcoRevive OS grew out of a real operational need.
          </h2>

          <p>
            The platform was not built first and given a
            recycling use case later. It emerged from the
            difficulty of managing a growing manual workflow.
          </p>
        </div>

        <div className="public-platform-flow">
          <span>Community requests</span>
          <ArrowRight />
          <span>Manual coordination</span>
          <ArrowRight />
          <span>Growing complexity</span>
          <ArrowRight />
          <strong>EcoRevive OS</strong>
        </div>
      </section>

      <section className="cta">
        <div>
          <span className="eyebrow">
            Small actions create collective impact
          </span>

          <h2>
            Your unused device can become the next responsible
            action.
          </h2>
        </div>

        <Link className="button button-light" to="/register">
          Get started
          <ArrowRight size={18} />
        </Link>
      </section>
    </PublicLayout>
  )
}
