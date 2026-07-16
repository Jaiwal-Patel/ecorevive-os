import {
  CalendarCheck,
  PackageCheck,
  Pencil,
  Plus,
  Recycle,
  Save,
  X,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  useMemo,
  useState,
  type FormEvent,
} from 'react'

import { api, errorMessage } from '../api/client'
import { Loading } from '../components/Loading'
import type {
  CollectionRequest,
  HandoverBatch,
  Paginated,
  PickupAssignment,
  VolunteerProfile,
} from '../types'

type AssignmentStatus =
  | 'proposed'
  | 'accepted'
  | 'declined'
  | 'completed'
  | 'cancelled'

interface AssignmentForm {
  request: string
  volunteer: string
  scheduled_for: string
  status: AssignmentStatus
  instructions: string
}

interface AssignmentEditForm {
  volunteer: string
  scheduled_for: string
  status: AssignmentStatus
  instructions: string
}

const emptyAssignment: AssignmentForm = {
  request: '',
  volunteer: '',
  scheduled_for: '',
  status: 'proposed',
  instructions: '',
}

const assignmentStatusLabels: Record<
  AssignmentStatus,
  string
> = {
  proposed: 'Proposed',
  accepted: 'Confirmed',
  declined: 'Declined',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

function toDateTimeLocal(value: string) {
  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  const localDate = new Date(
    date.getTime() - offset * 60 * 1000,
  )

  return localDate
    .toISOString()
    .slice(0, 16)
}

export function FulfillmentPage() {
  const queryClient = useQueryClient()

  const requests = useQuery({
    queryKey: ['requests'],
    queryFn: async () =>
      (
        await api.get<Paginated<CollectionRequest>>(
          '/collection-requests/?page_size=100',
        )
      ).data,
  })

  const volunteers = useQuery({
    queryKey: ['volunteers'],
    queryFn: async () =>
      (
        await api.get<Paginated<VolunteerProfile>>(
          '/volunteer-profiles/?page_size=100',
        )
      ).data,
  })

  const assignments = useQuery({
    queryKey: ['assignments'],
    queryFn: async () =>
      (
        await api.get<Paginated<PickupAssignment>>(
          '/pickup-assignments/?page_size=100',
        )
      ).data,
  })

  const batches = useQuery({
    queryKey: ['handovers'],
    queryFn: async () =>
      (
        await api.get<Paginated<HandoverBatch>>(
          '/handover-batches/?page_size=100',
        )
      ).data,
  })

  const [
    assignment,
    setAssignment,
  ] = useState<AssignmentForm>(
    emptyAssignment,
  )

  const [
    assignmentError,
    setAssignmentError,
  ] = useState('')

  const createAssignment = useMutation({
    mutationFn: () =>
      api.post(
        '/pickup-assignments/',
        assignment,
      ),
    onSuccess: () => {
      setAssignment(
        emptyAssignment,
      )
      setAssignmentError('')

      void queryClient.invalidateQueries({
        queryKey: ['assignments'],
      })
      void queryClient.invalidateQueries({
        queryKey: ['requests'],
      })
    },
    onError: (error) => {
      setAssignmentError(
        errorMessage(error),
      )
    },
  })

  const [
    editingAssignmentId,
    setEditingAssignmentId,
  ] = useState<string | null>(null)

  const [
    assignmentEdit,
    setAssignmentEdit,
  ] = useState<AssignmentEditForm>({
    volunteer: '',
    scheduled_for: '',
    status: 'proposed',
    instructions: '',
  })

  const [
    editAssignmentError,
    setEditAssignmentError,
  ] = useState('')

  const updateAssignment = useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id: string
      values: AssignmentEditForm
    }) =>
      api.patch(
        `/pickup-assignments/${id}/`,
        values,
      ),
    onSuccess: () => {
      setEditingAssignmentId(null)
      setEditAssignmentError('')

      void queryClient.invalidateQueries({
        queryKey: ['assignments'],
      })
      void queryClient.invalidateQueries({
        queryKey: ['requests'],
      })
    },
    onError: (error) => {
      setEditAssignmentError(
        errorMessage(error),
      )
    },
  })

  const collected = useMemo(
    () =>
      requests.data?.results.filter(
        (request) =>
          request.status === 'collected',
      ) ?? [],
    [requests.data],
  )

  const [
    selected,
    setSelected,
  ] = useState<Record<string, string>>({})

  const [
    batch,
    setBatch,
  ] = useState({
    reference: '',
    recycler_name: 'Enviroserve UAE',
    handover_date: '',
    receipt_number: '',
  })

  const [
    handoverError,
    setHandoverError,
  ] = useState('')

  const total = Object.values(
    selected,
  ).reduce(
    (sum, value) =>
      sum + (Number(value) || 0),
    0,
  )

  const createHandover = useMutation({
    mutationFn: () =>
      api.post(
        '/handover-batches/',
        {
          ...batch,
          total_weight_kg: String(total),
          handover_requests:
            Object.entries(selected)
              .filter(
                ([, weight]) =>
                  Number(weight) > 0,
              )
              .map(
                ([
                  request,
                  verified_weight_kg,
                ]) => ({
                  request,
                  verified_weight_kg,
                }),
              ),
        },
      ),
    onSuccess: () => {
      setSelected({})
      setBatch({
        reference: '',
        recycler_name:
          'Enviroserve UAE',
        handover_date: '',
        receipt_number: '',
      })
      setHandoverError('')

      void queryClient.invalidateQueries({
        queryKey: ['handovers'],
      })
      void queryClient.invalidateQueries({
        queryKey: ['requests'],
      })
    },
    onError: (error) => {
      setHandoverError(
        errorMessage(error),
      )
    },
  })

  if (
    requests.isLoading
    || volunteers.isLoading
    || assignments.isLoading
    || batches.isLoading
  ) {
    return <Loading />
  }

  const schedulable =
    requests.data?.results.filter(
      (request) =>
        request.status === 'approved',
    ) ?? []

  const eligibleVolunteers =
    volunteers.data?.results.filter(
      (volunteer) =>
        volunteer.can_receive_assignments,
    ) ?? []

  const assignmentRows =
    assignments.data?.results ?? []

  const beginEditingAssignment = (
    currentAssignment: PickupAssignment,
  ) => {
    setEditingAssignmentId(
      currentAssignment.id,
    )
    setEditAssignmentError('')

    setAssignmentEdit({
      volunteer:
        currentAssignment.volunteer,
      scheduled_for:
        toDateTimeLocal(
          currentAssignment.scheduled_for,
        ),
      status:
        currentAssignment.status as AssignmentStatus,
      instructions:
        currentAssignment.instructions,
    })
  }

  const cancelEditingAssignment = () => {
    setEditingAssignmentId(null)
    setEditAssignmentError('')
  }

  const submitAssignmentEdit = (
    event: FormEvent,
    id: string,
  ) => {
    event.preventDefault()

    updateAssignment.mutate({
      id,
      values: assignmentEdit,
    })
  }

  return (
    <div className="workspace">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            Scheduling and recycler verification
          </span>

          <h1>Fulfillment</h1>

          <p>
            Assign approved requests to volunteers, update or
            reassign pickups after contacting them, and reconcile
            collected items into certified handover batches.
          </p>
        </div>
      </div>

      <div className="fulfillment-grid">
        <form
          className="panel admin-form"
          onSubmit={(event: FormEvent) => {
            event.preventDefault()
            createAssignment.mutate()
          }}
        >
          <div className="panel-head">
            <div>
              <h2>
                <CalendarCheck size={19} />
                Create pickup assignment
              </h2>

              <p>
                Creating an assignment advances an approved request
                to Assigned.
              </p>
            </div>
          </div>

          <div className="form-stack">
            <label>
              Approved request

              <select
                required
                value={assignment.request}
                onChange={(event) =>
                  setAssignment({
                    ...assignment,
                    request:
                      event.target.value,
                  })
                }
              >
                <option value="">
                  Select request
                </option>

                {schedulable.map(
                  (request) => (
                    <option
                      key={request.id}
                      value={request.id}
                    >
                      {request.public_reference}
                      {' — '}
                      {request.area}
                      {' — '}
                      {request.requester_name}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Volunteer

              <select
                required
                value={assignment.volunteer}
                onChange={(event) =>
                  setAssignment({
                    ...assignment,
                    volunteer:
                      event.target.value,
                  })
                }
              >
                <option value="">
                  Select approved volunteer
                </option>

                {eligibleVolunteers.map(
                  (volunteer) => (
                    <option
                      key={volunteer.id}
                      value={volunteer.id}
                    >
                      {volunteer.user_name}
                      {' — '}
                      {volunteer.service_areas
                        || 'Area not recorded'}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label>
              Scheduled date and time

              <input
                type="datetime-local"
                required
                value={
                  assignment.scheduled_for
                }
                onChange={(event) =>
                  setAssignment({
                    ...assignment,
                    scheduled_for:
                      event.target.value,
                  })
                }
              />
            </label>

            <label>
              Instructions

              <textarea
                value={
                  assignment.instructions
                }
                onChange={(event) =>
                  setAssignment({
                    ...assignment,
                    instructions:
                      event.target.value,
                  })
                }
                placeholder="Contact details, access instructions, item notes, or pickup requirements."
              />
            </label>

            {eligibleVolunteers.length === 0 && (
              <div className="alert">
                No approved active volunteers are currently available
                for assignment.
              </div>
            )}

            {assignmentError && (
              <div className="alert alert-error">
                {assignmentError}
              </div>
            )}

            <button
              type="submit"
              className="button"
              disabled={
                createAssignment.isPending
                || schedulable.length === 0
                || eligibleVolunteers.length === 0
              }
            >
              <Plus size={18} />

              {createAssignment.isPending
                ? 'Creating…'
                : 'Create assignment'}
            </button>
          </div>
        </form>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Pickup assignments</h2>

              <p>
                Edit the volunteer, schedule, status, or instructions
                whenever the operational plan changes.
              </p>
            </div>
          </div>

          <div className="card-list">
            {assignmentRows.map(
              (currentAssignment) => {
                const isEditing =
                  editingAssignmentId
                  === currentAssignment.id

                if (isEditing) {
                  return (
                    <article
                      key={currentAssignment.id}
                    >
                      <div className="org-icon">
                        <CalendarCheck />
                      </div>

                      <form
                        className="form-stack"
                        onSubmit={(event) =>
                          submitAssignmentEdit(
                            event,
                            currentAssignment.id,
                          )
                        }
                      >
                        <div>
                          <strong>
                            {
                              currentAssignment.request_reference
                            }
                          </strong>

                          <small>
                            Update or reassign this pickup
                          </small>
                        </div>

                        <label>
                          Volunteer

                          <select
                            required
                            value={
                              assignmentEdit.volunteer
                            }
                            onChange={(event) =>
                              setAssignmentEdit({
                                ...assignmentEdit,
                                volunteer:
                                  event.target.value,
                              })
                            }
                          >
                            <option value="">
                              Select approved volunteer
                            </option>

                            {eligibleVolunteers.map(
                              (volunteer) => (
                                <option
                                  key={volunteer.id}
                                  value={
                                    volunteer.id
                                  }
                                >
                                  {
                                    volunteer.user_name
                                  }
                                  {' — '}
                                  {volunteer.service_areas
                                    || 'Area not recorded'}
                                </option>
                              ),
                            )}
                          </select>
                        </label>

                        <label>
                          Scheduled date and time

                          <input
                            type="datetime-local"
                            required
                            value={
                              assignmentEdit.scheduled_for
                            }
                            onChange={(event) =>
                              setAssignmentEdit({
                                ...assignmentEdit,
                                scheduled_for:
                                  event.target.value,
                              })
                            }
                          />
                        </label>

                        <label>
                          Status

                          <select
                            value={
                              assignmentEdit.status
                            }
                            onChange={(event) =>
                              setAssignmentEdit({
                                ...assignmentEdit,
                                status:
                                  event.target
                                    .value as AssignmentStatus,
                              })
                            }
                          >
                            {Object.entries(
                              assignmentStatusLabels,
                            ).map(
                              ([
                                value,
                                label,
                              ]) => (
                                <option
                                  key={value}
                                  value={value}
                                >
                                  {label}
                                </option>
                              ),
                            )}
                          </select>
                        </label>

                        <label>
                          Instructions or reassignment note

                          <textarea
                            value={
                              assignmentEdit.instructions
                            }
                            onChange={(event) =>
                              setAssignmentEdit({
                                ...assignmentEdit,
                                instructions:
                                  event.target.value,
                              })
                            }
                            placeholder="Record why the volunteer changed or why the schedule was revised."
                          />
                        </label>

                        {editAssignmentError && (
                          <div className="alert alert-error">
                            {editAssignmentError}
                          </div>
                        )}

                        <div>
                          <button
                            type="submit"
                            className="button button-small"
                            disabled={
                              updateAssignment.isPending
                            }
                          >
                            <Save size={16} />

                            {updateAssignment.isPending
                              ? 'Saving…'
                              : 'Save changes'}
                          </button>

                          <button
                            type="button"
                            className="button button-small button-ghost"
                            disabled={
                              updateAssignment.isPending
                            }
                            onClick={
                              cancelEditingAssignment
                            }
                          >
                            <X size={16} />
                            Cancel
                          </button>
                        </div>
                      </form>
                    </article>
                  )
                }

                return (
                  <article
                    key={currentAssignment.id}
                  >
                    <div className="org-icon">
                      <CalendarCheck />
                    </div>

                    <div>
                      <strong>
                        {
                          currentAssignment.request_reference
                        }
                      </strong>

                      <small>
                        {
                          currentAssignment.volunteer_name
                        }
                      </small>

                      <p>
                        {new Date(
                          currentAssignment.scheduled_for,
                        ).toLocaleString()}
                        {' · '}
                        {
                          assignmentStatusLabels[
                            currentAssignment.status as AssignmentStatus
                          ]
                        }
                      </p>

                      {currentAssignment.instructions && (
                        <p>
                          {
                            currentAssignment.instructions
                          }
                        </p>
                      )}
                    </div>

                    <button
                      type="button"
                      className="button button-small button-ghost"
                      onClick={() =>
                        beginEditingAssignment(
                          currentAssignment,
                        )
                      }
                    >
                      <Pencil size={16} />
                      Edit
                    </button>
                  </article>
                )
              },
            )}

            {assignmentRows.length === 0 && (
              <div className="empty compact">
                <p>No assignments yet.</p>
              </div>
            )}
          </div>
        </section>
      </div>

      <div className="fulfillment-grid handover-section">
        <form
          className="panel admin-form"
          onSubmit={(event: FormEvent) => {
            event.preventDefault()
            createHandover.mutate()
          }}
        >
          <div className="panel-head">
            <div>
              <h2>
                <Recycle size={19} />
                Record recycler handover
              </h2>

              <p>
                Enter only weights verified during the batch
                reconciliation.
              </p>
            </div>
          </div>

          <div className="form-stack">
            <label>
              Batch reference

              <input
                required
                value={batch.reference}
                onChange={(event) =>
                  setBatch({
                    ...batch,
                    reference:
                      event.target.value,
                  })
                }
                placeholder="ER-HO-2026-001"
              />
            </label>

            <label>
              Recycler

              <input
                required
                value={batch.recycler_name}
                onChange={(event) =>
                  setBatch({
                    ...batch,
                    recycler_name:
                      event.target.value,
                  })
                }
              />
            </label>

            <label>
              Handover date

              <input
                type="date"
                required
                value={batch.handover_date}
                onChange={(event) =>
                  setBatch({
                    ...batch,
                    handover_date:
                      event.target.value,
                  })
                }
              />
            </label>

            <label>
              Receipt number

              <input
                value={batch.receipt_number}
                onChange={(event) =>
                  setBatch({
                    ...batch,
                    receipt_number:
                      event.target.value,
                  })
                }
              />
            </label>

            <div className="handover-requests">
              <strong>
                Collected requests
              </strong>

              {collected.map(
                (request) => (
                  <label
                    className="handover-row"
                    key={request.id}
                  >
                    <input
                      type="checkbox"
                      checked={
                        selected[request.id]
                        !== undefined
                      }
                      onChange={(event) => {
                        const copy = {
                          ...selected,
                        }

                        if (
                          event.target.checked
                        ) {
                          copy[request.id] =
                            request.actual_weight_kg
                            || request.estimated_weight_kg
                            || ''
                        } else {
                          delete copy[
                            request.id
                          ]
                        }

                        setSelected(copy)
                      }}
                    />

                    <span>
                      {
                        request.public_reference
                      }

                      <small>
                        {request.area}
                        {' · '}
                        {request.items.length}
                        {' item types'}
                      </small>
                    </span>

                    <input
                      aria-label={`Verified weight for ${request.public_reference}`}
                      type="number"
                      min="0.01"
                      step="0.01"
                      disabled={
                        selected[request.id]
                        === undefined
                      }
                      value={
                        selected[request.id]
                        ?? ''
                      }
                      onChange={(event) =>
                        setSelected({
                          ...selected,
                          [request.id]:
                            event.target.value,
                        })
                      }
                      placeholder="kg"
                    />
                  </label>
                ),
              )}

              {collected.length === 0 && (
                <p className="muted">
                  No requests are awaiting handover.
                </p>
              )}
            </div>

            <div className="total-row">
              <span>
                Verified batch total
              </span>

              <strong>
                {total.toFixed(2)} kg
              </strong>
            </div>

            {handoverError && (
              <div className="alert alert-error">
                {handoverError}
              </div>
            )}

            <button
              type="submit"
              className="button"
              disabled={
                createHandover.isPending
                || total <= 0
              }
            >
              <PackageCheck size={18} />

              {createHandover.isPending
                ? 'Recording…'
                : 'Record handover'}
            </button>
          </div>
        </form>

        <section className="panel">
          <div className="panel-head">
            <h2>Recent handovers</h2>
          </div>

          <div className="card-list">
            {(
              batches.data?.results ?? []
            ).map((handover) => (
              <article key={handover.id}>
                <div className="org-icon">
                  <Recycle />
                </div>

                <div>
                  <strong>
                    {handover.reference}
                  </strong>

                  <small>
                    {handover.recycler_name}
                  </small>

                  <p>
                    {handover.handover_date}
                    {' · '}
                    {
                      handover.included_requests
                        ?.length ?? 0
                    }
                    {' requests'}
                  </p>
                </div>

                <span>
                  {handover.total_weight_kg} kg
                </span>
              </article>
            ))}

            {(
              batches.data?.results ?? []
            ).length === 0 && (
              <div className="empty compact">
                <p>
                  No handover batches yet.
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}