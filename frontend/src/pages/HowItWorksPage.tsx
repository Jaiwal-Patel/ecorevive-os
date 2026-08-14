import {
  ArrowRight,
  BadgeCheck,
  Boxes,
  CalendarCheck,
  ClipboardList,
  Recycle,
  ShieldCheck,
  Truck,
  UserCheck,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { PublicLayout } from '../components/PublicLayout'

const processSteps = [
  {
    number: '01',
    icon: <ClipboardList size={26} />,
    title: 'Submit a request',
    text: 'Create an account and tell EcoRevive what you would like collected, where it is located and any useful pickup details.',
  },
  {
    number: '02',
    icon: <UserCheck size={26} />,
    title: 'Review & coordinate',
    text: 'EcoRevive reviews the request, confirms that it fits the collection workflow and prepares it for scheduling.',
  },
  {
    number: '03',
    icon: <CalendarCheck size={26} />,
    title: 'Schedule & collect',
    text: 'A pickup is coordinated and, where appropriate, assigned to an approved volunteer for collection.',
  },
  {
    number: '04',
    icon: <Boxes size={26} />,
    title: 'Aggregate',
    text: 'Collected material is consolidated so individual household contributions can move efficiently into recycler handover.',
  },
  {
    number: '05',
    icon: <BadgeCheck size={26} />,
    title: 'Handover & verify',
    text: 'Material is transferred into professional recycling infrastructure and verified weights can be recorded against the handover.',
  },
]

export function HowItWorksPage() {
  return (
    <PublicLayout>
      <section className="public-inner-hero">
        <div className="public-inner-hero-copy">
          <span className="eyebrow">
            <Recycle size={15} />
            How EcoRevive works
          </span>

          <h1>
            From an unused device to responsible recycling.
          </h1>

          <p>
            EcoRevive turns what can be a confusing disposal
            problem into a clear sequence: request, coordinate,
            collect, aggregate and hand over responsibly.
          </p>

          <div className="hero-actions">
            <Link className="button" to="/register">
              Request a pickup
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>

        <aside className="public-hero-principle">
          <span>The goal</span>

          <strong>
            Make the responsible choice the convenient choice.
          </strong>

          <p>
            Residents should not need to research recycling
            facilities, organize transport and navigate the
            process independently.
          </p>
        </aside>
      </section>

      <section className="section">
        <div className="section-heading">
          <span className="eyebrow">
            The collection journey
          </span>

          <h2>
            Five stages. One connected workflow.
          </h2>
        </div>

        <div className="process-grid">
          {processSteps.map((step) => (
            <article
              className="process-card"
              key={step.number}
            >
              <span className="process-number">
                {step.number}
              </span>

              <div className="process-icon">
                {step.icon}
              </div>

              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section public-split">
        <div className="public-copy-block">
          <span className="eyebrow">
            For residents
          </span>

          <h2>
            What you need to do.
          </h2>

          <p>
            The resident side is intentionally simple. EcoRevive
            handles the operational complexity behind the
            scenes.
          </p>

          <div className="public-checklist">
            <div>
              <span>1</span>
              <p>
                <strong>Create your account.</strong>
                Resident email is optional; a phone number can
                be used when no email is provided.
              </p>
            </div>

            <div>
              <span>2</span>
              <p>
                <strong>Describe the collection.</strong>
                Add the items, location, preferred timing and
                any access instructions.
              </p>
            </div>

            <div>
              <span>3</span>
              <p>
                <strong>Track the request.</strong>
                Your account keeps the request and its progress
                together in one place.
              </p>
            </div>
          </div>
        </div>

        <div className="public-proof-card public-proof-light">
          <ShieldCheck size={34} />

          <span>Privacy by design</span>

          <strong>
            Personal collection details are operational data,
            not public impact data.
          </strong>

          <p>
            Addresses and account information remain inside the
            authenticated workflow. Public reporting uses
            aggregated figures.
          </p>
        </div>
      </section>

      <section className="section audience">
        <div>
          <span className="eyebrow">
            For volunteers
          </span>

          <h2>
            Volunteer access is structured, not automatic.
          </h2>

          <p>
            Volunteers can register through the same platform,
            but applications are reviewed before volunteers can
            receive pickup assignments.
          </p>
        </div>

        <div className="public-mission-points">
          <div>
            <UserCheck />
            <span>
              <strong>Register</strong>
              Submit a volunteer application.
            </span>
          </div>

          <div>
            <BadgeCheck />
            <span>
              <strong>Get approved</strong>
              EcoRevive reviews the application.
            </span>
          </div>

          <div>
            <Truck />
            <span>
              <strong>Receive assignments</strong>
              Approved volunteers can help with collections.
            </span>
          </div>
        </div>
      </section>

      <section className="section public-after-collection">
        <div className="section-heading">
          <span className="eyebrow">
            After collection
          </span>

          <h2>
            The material still has somewhere to go.
          </h2>

          <p className="public-section-lead">
            Collection alone is not the environmental outcome.
            EcoRevive consolidates collected material for
            transfer into established recycler infrastructure.
          </p>
        </div>

        <div className="public-after-flow">
          <span>
            <Truck />
            Collected
          </span>

          <ArrowRight />

          <span>
            <Boxes />
            Aggregated
          </span>

          <ArrowRight />

          <span>
            <Recycle />
            Recycler handover
          </span>

          <ArrowRight />

          <span>
            <BadgeCheck />
            Impact recorded
          </span>
        </div>
      </section>

      <section className="section public-enviroserve-section">
        <div className="public-copy-block">
          <span className="eyebrow">
            Downstream recycling partner
          </span>

          <h2>
            Handover to a recycler working directly with
            Dubai Municipality.
          </h2>

          <p>
            EcoRevive's electronic-waste collections are
            transferred to Enviroserve UAE for downstream
            recycling. In June 2026, Dubai Municipality and
            Enviroserve signed a strategic Memorandum of
            Cooperation covering safe e-waste collection,
            recycling and recovery of valuable materials.
          </p>

          <p>
            The agreement supports the Dubai Integrated Waste
            Management Strategy 2041 and the Circular Dubai
            initiative, placing Enviroserve within Dubai's
            formal public-private framework for responsible
            electronic-waste management.
          </p>

          <div className="public-independence-note">
            EcoRevive remains an independent community
            initiative. The official government collaboration
            described here is between Dubai Municipality and
            Enviroserve, EcoRevive's downstream recycler.
          </div>

          <div className="public-source-links">
            <a
              href="https://www.tadweer.ae/media/dubai-municipality-and-enviroserve-sign-strategic-agreement-to-enhance-e-waste-recycling-and-support-circular-economy-in-dubai"
              target="_blank"
              rel="noreferrer"
            >
              Dubai Municipality partnership
              <ArrowRight size={15} />
            </a>

            <a
              href="https://dubaiindustrialcity.ae/media/press-release/enviroserve-launches-world-largest-integrated-e-waste-and-specialised-recycling-plant"
              target="_blank"
              rel="noreferrer"
            >
              Recycling Hub facility details
              <ArrowRight size={15} />
            </a>
          </div>
        </div>

        <div className="public-enviroserve-credentials">
          <article>
            <BadgeCheck />

            <span>June 2026</span>

            <strong>
              Strategic agreement with Dubai Municipality
            </strong>

            <p>
              Cooperation on safe electronic-waste collection,
              recycling and resource recovery across Dubai.
            </p>
          </article>

          <article>
            <Recycle />

            <span>39,000 tonnes / year</span>

            <strong>
              Dedicated e-waste processing capacity
            </strong>

            <p>
              Published annual electronic and electrical waste
              capacity of Enviroserve's Dubai Recycling Hub.
            </p>
          </article>

          <article>
            <ShieldCheck />

            <span>96% reported recovery</span>

            <strong>
              High material-recovery capability
            </strong>

            <p>
              Dubai Industrial City reports a 96% recovery rate
              for the facility's mechanical separation process.
            </p>
          </article>

          <article>
            <BadgeCheck />

            <span>AED 120 million facility</span>

            <strong>
              Swiss-government export-finance backing
            </strong>

            <p>
              The Recycling Hub project was backed at launch by
              the Swiss Government Export Finance Agency.
            </p>
          </article>
        </div>
      </section>

      <section className="cta">
        <div>
          <span className="eyebrow">
            Ready when you are
          </span>

          <h2>
            Start a collection request in a few minutes.
          </h2>
        </div>

        <Link className="button button-light" to="/register">
          Create an account
          <ArrowRight size={18} />
        </Link>
      </section>
    </PublicLayout>
  )
}
