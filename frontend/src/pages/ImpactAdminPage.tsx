import { Save } from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { useState } from 'react'

import { api, errorMessage } from '../api/client'
import { Loading } from '../components/Loading'
import type { ImpactMetric, Paginated } from '../types'

type MetricRowProps = {
  metric: ImpactMetric
}

function MetricRow({ metric }: MetricRowProps) {
  const queryClient = useQueryClient()
  const [value, setValue] = useState(String(metric.value))

  const mutation = useMutation({
    mutationFn: async () => {
      return api.patch(
        `/impact-metrics/${metric.id}/`,
        {
          value,
        },
      )
    },

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['impact-admin'],
        }),
        queryClient.invalidateQueries({
          queryKey: ['public-impact'],
        }),
      ])
    },
  })

  const saveMetric = () => {
    if (mutation.isPending) {
      return
    }

    mutation.mutate()
  }

  return (
    <article className="impact-metric-row">
      <div className="impact-metric-copy">
        <strong>{metric.label}</strong>

        {metric.description && (
          <small>{metric.description}</small>
        )}
      </div>

      <div className="impact-metric-editor">
        <div className="impact-value-control">
          <input
            type="number"
            min="0"
            step="0.01"
            value={value}
            aria-label={`${metric.label} value`}
            onChange={(event) =>
              setValue(event.target.value)
            }
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                saveMetric()
              }
            }}
          />

          <span className="impact-value-unit">
            {metric.unit}
          </span>
        </div>

        <button
          type="button"
          className="impact-save-button"
          aria-label={`Save ${metric.label}`}
          title={`Save ${metric.label}`}
          disabled={mutation.isPending}
          onClick={saveMetric}
        >
          <Save size={18} />
        </button>
      </div>

      {mutation.isError && (
        <p className="impact-metric-error">
          {errorMessage(mutation.error)}
        </p>
      )}

      {mutation.isSuccess && (
        <p className="impact-metric-success">
          Saved
        </p>
      )}
    </article>
  )
}

export function ImpactAdminPage() {
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['impact-admin'],

    queryFn: async () => {
      const response =
        await api.get<Paginated<ImpactMetric>>(
          '/impact-metrics/?page_size=100',
        )

      return response.data
    },
  })

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="workspace narrow impact-admin-page">
      <style>{`
        .impact-admin-page {
          width: 100%;
          max-width: 1120px;
        }

        .impact-admin-panel {
          overflow: visible;
        }

        .impact-verification-rule {
          margin: 0;
          padding: 15px 18px;
          border: 1px solid #eadba9;
          border-radius: 14px 14px 0 0;
          background: #fff9e7;
          color: #6f5819;
          font-size: 0.9rem;
          line-height: 1.55;
        }

        .impact-verification-rule strong {
          font-weight: 800;
        }

        .impact-metric-list {
          padding: 10px 24px;
        }

        .impact-metric-row {
          display: grid;
          grid-template-columns:
            minmax(0, 1fr)
            minmax(290px, auto);
          column-gap: 28px;
          align-items: center;
          min-height: 82px;
          padding: 16px 0;
          border-bottom: 1px solid var(--line);
        }

        .impact-metric-row:last-child {
          border-bottom: 0;
        }

        .impact-metric-copy {
          min-width: 0;
        }

        .impact-metric-copy strong,
        .impact-metric-copy small {
          display: block;
        }

        .impact-metric-copy strong {
          color: var(--ink);
          font-size: 0.96rem;
          line-height: 1.4;
        }

        .impact-metric-copy small {
          margin-top: 5px;
          color: var(--muted);
          font-size: 0.8rem;
          line-height: 1.45;
        }

        .impact-metric-editor {
          display: grid;
          grid-template-columns:
            minmax(220px, 1fr)
            42px;
          gap: 12px;
          align-items: center;
          justify-self: end;
          width: min(100%, 330px);
        }

        .impact-value-control {
          display: grid;
          grid-template-columns:
            minmax(110px, 1fr)
            max-content;
          align-items: stretch;
          min-width: 0;
        }

        .impact-value-control input {
          min-width: 0;
          height: 44px;
          padding: 10px 12px;
          border-radius: 10px 0 0 10px;
        }

        .impact-value-unit {
          display: flex;
          align-items: center;
          justify-content: center;
          min-width: 50px;
          max-width: 125px;
          padding: 0 13px;
          border: 1px solid #ccd9d2;
          border-left: 0;
          border-radius: 0 10px 10px 0;
          background: #edf3f0;
          color: var(--ink);
          font-size: 0.88rem;
          font-weight: 500;
          white-space: nowrap;
        }

        .impact-save-button {
          display: inline-grid;
          place-items: center;
          width: 42px;
          height: 42px;
          padding: 0;
          border: 0;
          border-radius: 10px;
          background: transparent;
          color: var(--green-dark);
        }

        .impact-save-button:hover {
          background: var(--soft);
          color: var(--green);
        }

        .impact-save-button:focus-visible {
          outline: 3px solid rgba(10, 92, 69, 0.16);
          outline-offset: 2px;
        }

        .impact-save-button:disabled {
          opacity: 0.45;
          cursor: not-allowed;
        }

        .impact-metric-error,
        .impact-metric-success {
          grid-column: 2;
          justify-self: start;
          margin: -8px 0 8px;
          font-size: 0.78rem;
          font-weight: 700;
        }

        .impact-metric-error {
          color: var(--danger);
        }

        .impact-metric-success {
          color: var(--green);
        }

        .impact-page-error {
          margin-top: 20px;
        }

        @media (max-width: 800px) {
          .impact-metric-row {
            grid-template-columns: 1fr;
            gap: 14px;
            padding: 20px 0;
          }

          .impact-metric-editor {
            grid-template-columns:
              minmax(0, 1fr)
              42px;
            justify-self: stretch;
            width: 100%;
          }

          .impact-metric-error,
          .impact-metric-success {
            grid-column: 1;
            margin: -5px 0 0;
          }
        }

        @media (max-width: 480px) {
          .impact-metric-list {
            padding: 8px 18px;
          }

          .impact-value-control {
            grid-template-columns:
              minmax(80px, 1fr)
              max-content;
          }

          .impact-value-unit {
            min-width: 44px;
            max-width: 100px;
            padding: 0 10px;
            font-size: 0.8rem;
          }
        }
      `}</style>

      <div className="page-head">
        <div>
          <span className="eyebrow">
            Public evidence
          </span>

          <h1>Impact metrics</h1>

          <p>
            Update verified totals without changing code.
            Public pages read these values directly from the
            database.
          </p>
        </div>
      </div>

      {isError && (
        <div className="alert alert-error impact-page-error">
          {errorMessage(error)}
        </div>
      )}

      <section className="panel impact-admin-panel">
        <p className="impact-verification-rule">
          <strong>Verification rule:</strong>{' '}
          update figures only from collection and recycler
          evidence. Keep calculation methods in the impact
          methodology document.
        </p>

        <div className="impact-metric-list">
          {(data?.results ?? []).map((metric) => (
            <MetricRow
              key={`${metric.id}-${metric.value}`}
              metric={metric}
            />
          ))}
        </div>
      </section>
    </div>
  )
}