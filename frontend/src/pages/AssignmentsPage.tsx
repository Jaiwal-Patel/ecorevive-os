import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  CalendarDays,
  Check,
  ClipboardCheck,
  MapPin,
  RefreshCw,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { api, errorMessage } from '../api/client'
import { Loading } from '../components/Loading'
import { StatusBadge } from '../components/StatusBadge'
import type {
  AssignmentStatus,
  Paginated,
  PickupAssignment,
} from '../types'

type AssignmentFilter = 'all' | AssignmentStatus

const statusOptions: Array<{
  value: AssignmentFilter
  label: string
}> = [
  {
    value: 'all',
    label: 'All assignments',
  },
  {
    value: 'proposed',
    label: 'Awaiting response',
  },
  {
    value: 'accepted',
    label: 'Accepted',
  },
  {
    value: 'declined',
    label: 'Declined',
  },
  {
    value: 'completed',
    label: 'Completed',
  },
  {
    value: 'cancelled',
    label: 'Cancelled',
  },
]

function formatDateTime(value: string | null) {
  if (!value) {
    return 'Not recorded'
  }

  return new Intl.DateTimeFormat('en-AE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function extractAssignments(
  data:
    | Paginated<PickupAssignment>
    | PickupAssignment[]
    | undefined,
) {
  if (!data) {
    return []
  }

  return Array.isArray(data)
    ? data
    : data.results
}

export function AssignmentsPage() {
  const queryClient = useQueryClient()

  const [statusFilter, setStatusFilter] =
    useState<AssignmentFilter>('all')
  const [decliningId, setDecliningId] =
    useState<string | null>(null)
  const [declineReason, setDeclineReason] =
    useState('')
  const [actionError, setActionError] =
    useState('')

  const {
    data,
    error,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: [
      'pickup-assignments',
      'mine',
      statusFilter,
    ],
    queryFn: async () => {
      const params =
        statusFilter === 'all'
          ? undefined
          : {
              status: statusFilter,
            }

      const response = await api.get<
        | Paginated<PickupAssignment>
        | PickupAssignment[]
      >('/pickup-assignments/mine/', {
        params,
      })

      return response.data
    },
  })

  const assignments = extractAssignments(data)

  const acceptMutation = useMutation({
    mutationFn: async (
      assignmentId: string,
    ) => {
      const response =
        await api.post<PickupAssignment>(
          `/pickup-assignments/${assignmentId}/accept/`,
          {},
        )

      return response.data
    },
    onSuccess: async () => {
      setActionError('')

      await queryClient.invalidateQueries({
        queryKey: [
          'pickup-assignments',
        ],
      })

      await queryClient.invalidateQueries({
        queryKey: ['requests'],
      })
    },
    onError: (mutationError) => {
      setActionError(
        errorMessage(mutationError),
      )
    },
  })

  const declineMutation = useMutation({
    mutationFn: async ({
      assignmentId,
      reason,
    }: {
      assignmentId: string
      reason: string
    }) => {
      const response =
        await api.post<PickupAssignment>(
          `/pickup-assignments/${assignmentId}/decline/`,
          {
            decline_reason: reason,
          },
        )

      return response.data
    },
    onSuccess: async () => {
      setActionError('')
      setDecliningId(null)
      setDeclineReason('')

      await queryClient.invalidateQueries({
        queryKey: [
          'pickup-assignments',
        ],
      })
    },
    onError: (mutationError) => {
      setActionError(
        errorMessage(mutationError),
      )
    },
  })

  function beginDecline(
    assignmentId: string,
  ) {
    setActionError('')
    setDeclineReason('')
    setDecliningId(assignmentId)
  }

  function cancelDecline() {
    if (declineMutation.isPending) {
      return
    }

    setActionError('')
    setDecliningId(null)
    setDeclineReason('')
  }

  function confirmDecline() {
    if (!decliningId) {
      return
    }

    const reason = declineReason.trim()

    if (!reason) {
      setActionError(
        'A reason is required when declining an assignment.',
      )
      return
    }

    declineMutation.mutate({
      assignmentId: decliningId,
      reason,
    })
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="workspace">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            Volunteer operations
          </span>

          <h1>My assignments</h1>

          <p>
            Review pickup assignments and
            accept or decline new requests.
          </p>
        </div>

        <button
          className="button"
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw size={18} />
          {isFetching
            ? 'Refreshing…'
            : 'Refresh'}
        </button>
      </div>

      <section className="panel">
        <div className="filters">
          <label className="select-control">
            <ClipboardCheck size={18} />

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target
                    .value as AssignmentFilter,
                )
              }
            >
              {statusOptions.map(
                (option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ),
              )}
            </select>
          </label>
        </div>

        {error ? (
          <div className="alert alert-error">
            {errorMessage(error)}
          </div>
        ) : null}

        {actionError ? (
          <div className="alert alert-error">
            {actionError}
          </div>
        ) : null}

        {assignments.length === 0 ? (
          <div className="empty">
            <ClipboardCheck />

            <h3>No assignments found</h3>

            <p>
              Pickup assignments will appear
              here when an administrator
              assigns them to you.
            </p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Request</th>
                  <th>Schedule</th>
                  <th>Location</th>
                  <th>Instructions</th>
                  <th>Status</th>
                  <th>Response</th>
                </tr>
              </thead>

              <tbody>
                {assignments.map(
                  (assignment) => (
                    <tr key={assignment.id}>
                      <td>
                        <Link
                          to={`/requests/${assignment.request}`}
                        >
                          <strong>
                            {
                              assignment.request_reference
                            }
                          </strong>
                        </Link>
                      </td>

                      <td>
                        <CalendarDays
                          size={16}
                        />{' '}
                        {formatDateTime(
                          assignment.scheduled_for,
                        )}
                      </td>

                      <td>
                        <MapPin size={16} />{' '}
                        {
                          assignment.request_address
                        }
                        <br />
                        {
                          assignment.request_area
                        }
                        ,{' '}
                        {
                          assignment.request_city
                        }
                      </td>

                      <td>
                        {assignment.instructions ||
                          'No assignment instructions'}

                        {assignment.request_access_instructions ? (
                          <>
                            <br />
                            <small>
                              Access:{' '}
                              {
                                assignment.request_access_instructions
                              }
                            </small>
                          </>
                        ) : null}
                      </td>

                      <td>
                        <StatusBadge
                          status={
                            assignment.status
                          }
                        />

                        {assignment.accepted_at ? (
                          <small>
                            <br />
                            Accepted{' '}
                            {formatDateTime(
                              assignment.accepted_at,
                            )}
                          </small>
                        ) : null}

                        {assignment.declined_at ? (
                          <small>
                            <br />
                            Declined{' '}
                            {formatDateTime(
                              assignment.declined_at,
                            )}
                          </small>
                        ) : null}
                      </td>

                      <td>
                        {assignment.is_awaiting_response &&
                        decliningId !==
                          assignment.id ? (
                          <div className="actions">
                            <button
                              className="button button-small"
                              type="button"
                              onClick={() =>
                                acceptMutation.mutate(
                                  assignment.id,
                                )
                              }
                              disabled={
                                acceptMutation.isPending ||
                                declineMutation.isPending ||
                                !assignment.can_be_accepted
                              }
                            >
                              <Check size={16} />
                              Accept
                            </button>

                            <button
                              className="button button-small button-secondary"
                              type="button"
                              onClick={() =>
                                beginDecline(
                                  assignment.id,
                                )
                              }
                              disabled={
                                acceptMutation.isPending ||
                                declineMutation.isPending ||
                                !assignment.can_be_declined
                              }
                            >
                              <X size={16} />
                              Decline
                            </button>
                          </div>
                        ) : null}

                        {decliningId ===
                        assignment.id ? (
                          <div>
                            <label className="field">
                              <span>
                                Reason for declining
                              </span>

                              <textarea
                                rows={3}
                                maxLength={2000}
                                value={declineReason}
                                onChange={(event) =>
                                  setDeclineReason(
                                    event.target
                                      .value,
                                  )
                                }
                                placeholder="Explain why you cannot complete this pickup."
                                autoFocus
                              />
                            </label>

                            <div className="actions">
                              <button
                                className="button button-small"
                                type="button"
                                onClick={
                                  confirmDecline
                                }
                                disabled={
                                  declineMutation.isPending ||
                                  !declineReason.trim()
                                }
                              >
                                Confirm decline
                              </button>

                              <button
                                className="button button-small button-secondary"
                                type="button"
                                onClick={
                                  cancelDecline
                                }
                                disabled={
                                  declineMutation.isPending
                                }
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : null}

                        {assignment.status ===
                        'declined' ? (
                          <small>
                            {assignment.decline_reason}
                          </small>
                        ) : null}

                        {assignment.status !==
                          'proposed' &&
                        assignment.status !==
                          'declined' ? (
                          <small>
                            No response required
                          </small>
                        ) : null}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}