import {
  Building2,
  CheckCircle2,
  Clock3,
  Plus,
  ShieldCheck,
  UserPlus,
  Users,
  XCircle,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  useState,
  type FormEvent,
} from 'react'

import { api, errorMessage } from '../api/client'
import { Loading } from '../components/Loading'
import { useAuth } from '../context/AuthContext'
import type {
  AdminUser,
  Organization,
  Paginated,
  UserRole,
  VolunteerApprovalStatus,
  VolunteerProfile,
} from '../types'

const roleLabels: Record<UserRole, string> = {
  founder_guardian: 'Founder Guardian',
  founder_recovery: 'Founder Recovery',
  principal_admin: 'Principal Administrator',
  operations_admin: 'Operations Administrator',
  volunteer: 'Volunteer',
  corporate_coordinator: 'Corporate Coordinator',
  resident: 'Resident',
}

const approvalLabels: Record<VolunteerApprovalStatus, string> = {
  pending: 'Pending review',
  approved: 'Approved',
  rejected: 'Rejected',
}

type AdministrationSection =
  | 'people'
  | 'volunteers'
  | 'organizations'

type VolunteerReviewDecision =
  | 'approved'
  | 'rejected'

interface VolunteerReviewPayload {
  id: string
  decision: VolunteerReviewDecision
  review_note: string
}

function getResults<T>(
  data: Paginated<T> | T[] | undefined,
): T[] {
  if (!data) {
    return []
  }

  if (Array.isArray(data)) {
    return data
  }

  return data.results
}

function formatDate(value: string | null) {
  if (!value) {
    return 'Not reviewed'
  }

  return new Date(value).toLocaleString()
}

export function AdministrationPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const [section, setSection] =
    useState<AdministrationSection>('people')

  const users = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () =>
      (
        await api.get<Paginated<AdminUser>>(
          '/users/?page_size=100',
        )
      ).data,
  })

  const volunteers = useQuery({
    queryKey: ['volunteers'],
    queryFn: async () =>
      (
        await api.get<
          Paginated<VolunteerProfile> | VolunteerProfile[]
        >('/volunteer-profiles/?page_size=100')
      ).data,
  })

  const pendingVolunteers = useQuery({
    queryKey: ['pending-volunteers'],
    queryFn: async () =>
      (
        await api.get<
          Paginated<VolunteerProfile> | VolunteerProfile[]
        >('/volunteer-profiles/pending/?page_size=100')
      ).data,
  })

  const organizations = useQuery({
    queryKey: ['organizations'],
    queryFn: async () =>
      (
        await api.get<Paginated<Organization>>(
          '/organizations/?page_size=100',
        )
      ).data,
  })

  const [newUser, setNewUser] = useState({
    email: '',
    full_name: '',
    phone_number: '',
    role: 'resident' as UserRole,
    password: '',
  })

  const [userError, setUserError] = useState('')

  const createUser = useMutation({
    mutationFn: () =>
      api.post(
        '/users/',
        newUser,
      ),
    onSuccess: () => {
      setNewUser({
        email: '',
        full_name: '',
        phone_number: '',
        role: 'resident',
        password: '',
      })
      setUserError('')

      void queryClient.invalidateQueries({
        queryKey: ['admin-users'],
      })
    },
    onError: (error) => {
      setUserError(
        errorMessage(error),
      )
    },
  })

  const [newVolunteer, setNewVolunteer] = useState({
    user: '',
    service_areas: 'Dubai',
    has_vehicle: false,
    vehicle_description: '',
    capacity_kg: '0',
    availability_notes: '',
    active: false,
    safety_acknowledged: false,
  })

  const [volunteerError, setVolunteerError] =
    useState('')

  const createVolunteer = useMutation({
    mutationFn: () =>
      api.post(
        '/volunteer-profiles/',
        newVolunteer,
      ),
    onSuccess: () => {
      setNewVolunteer({
        user: '',
        service_areas: 'Dubai',
        has_vehicle: false,
        vehicle_description: '',
        capacity_kg: '0',
        availability_notes: '',
        active: false,
        safety_acknowledged: false,
      })
      setVolunteerError('')

      void queryClient.invalidateQueries({
        queryKey: ['volunteers'],
      })
      void queryClient.invalidateQueries({
        queryKey: ['pending-volunteers'],
      })
    },
    onError: (error) => {
      setVolunteerError(
        errorMessage(error),
      )
    },
  })

  const [reviewNotes, setReviewNotes] =
    useState<Record<string, string>>({})

  const [reviewError, setReviewError] =
    useState('')

  const reviewVolunteer = useMutation({
    mutationFn: ({
      id,
      decision,
      review_note,
    }: VolunteerReviewPayload) =>
      api.post(
        `/volunteer-profiles/${id}/review/`,
        {
          decision,
          review_note,
        },
      ),
    onSuccess: (_response, variables) => {
      setReviewError('')

      setReviewNotes((current) => {
        const next = {
          ...current,
        }

        delete next[variables.id]

        return next
      })

      void queryClient.invalidateQueries({
        queryKey: ['volunteers'],
      })
      void queryClient.invalidateQueries({
        queryKey: ['pending-volunteers'],
      })
    },
    onError: (error) => {
      setReviewError(
        errorMessage(error),
      )
    },
  })

  const [newOrganization, setNewOrganization] =
    useState({
      name: '',
      organization_type: 'corporate',
      contact_email: '',
      contact_phone: '',
      address: '',
    })

  const [organizationError, setOrganizationError] =
    useState('')

  const approveOrganization = useMutation({
    mutationFn: (id: string) =>
      api.post(
        `/organizations/${id}/approve/`,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['organizations'],
      })
    },
  })

  const createOrganization = useMutation({
    mutationFn: () =>
      api.post(
        '/organizations/',
        newOrganization,
      ),
    onSuccess: () => {
      setNewOrganization({
        name: '',
        organization_type: 'corporate',
        contact_email: '',
        contact_phone: '',
        address: '',
      })
      setOrganizationError('')

      void queryClient.invalidateQueries({
        queryKey: ['organizations'],
      })
    },
    onError: (error) => {
      setOrganizationError(
        errorMessage(error),
      )
    },
  })

  if (
    users.isLoading
    || volunteers.isLoading
    || pendingVolunteers.isLoading
    || organizations.isLoading
  ) {
    return <Loading />
  }

  const allowedRoles: UserRole[] =
    user?.role === 'operations_admin'
      ? [
          'resident',
          'volunteer',
          'corporate_coordinator',
        ]
      : user?.role === 'principal_admin'
        ? [
            'resident',
            'volunteer',
            'corporate_coordinator',
            'operations_admin',
          ]
        : [
            'resident',
            'volunteer',
            'corporate_coordinator',
            'operations_admin',
            'principal_admin',
          ]

  const userRows =
    users.data?.results ?? []

  const volunteerRows =
    getResults(volunteers.data)

  const pendingVolunteerRows =
    getResults(pendingVolunteers.data)

  const organizationRows =
    organizations.data?.results ?? []

  const availableVolunteerUsers =
    userRows.filter(
      (candidate) =>
        candidate.role === 'volunteer'
        && !volunteerRows.some(
          (profile) =>
            profile.user === candidate.id,
        ),
    )

  const submitVolunteerReview = (
    volunteer: VolunteerProfile,
    decision: VolunteerReviewDecision,
  ) => {
    const note =
      reviewNotes[volunteer.id]?.trim() ?? ''

    if (
      decision === 'rejected'
      && !note
    ) {
      setReviewError(
        'Enter a reason before rejecting a volunteer application.',
      )
      return
    }

    setReviewError('')

    reviewVolunteer.mutate({
      id: volunteer.id,
      decision,
      review_note: note,
    })
  }

  return (
    <div className="workspace">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            People and partner setup
          </span>

          <h1>Administration</h1>

          <p>
            Manage operational identities, volunteer applications,
            volunteer profiles, and participating organizations.
          </p>
        </div>
      </div>

      <div className="tabs">
        <button
          type="button"
          className={
            section === 'people'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection('people')
          }
        >
          <Users size={17} />
          People
        </button>

        <button
          type="button"
          className={
            section === 'volunteers'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection('volunteers')
          }
        >
          <UserPlus size={17} />
          Volunteers

          {pendingVolunteerRows.length > 0 && (
            <span>
              {pendingVolunteerRows.length}
            </span>
          )}
        </button>

        <button
          type="button"
          className={
            section === 'organizations'
              ? 'active'
              : ''
          }
          onClick={() =>
            setSection('organizations')
          }
        >
          <Building2 size={17} />
          Organizations
        </button>
      </div>

      {section === 'people' && (
        <div className="admin-split">
          <form
            className="panel admin-form"
            onSubmit={(event: FormEvent) => {
              event.preventDefault()
              createUser.mutate()
            }}
          >
            <div className="panel-head">
              <h2>Create user</h2>
            </div>

            <div className="form-stack">
              <label>
                Full name

                <input
                  required
                  value={newUser.full_name}
                  onChange={(event) =>
                    setNewUser({
                      ...newUser,
                      full_name: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Email

                <input
                  type="email"
                  required
                  value={newUser.email}
                  onChange={(event) =>
                    setNewUser({
                      ...newUser,
                      email: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Phone / WhatsApp

                <input
                  value={newUser.phone_number}
                  onChange={(event) =>
                    setNewUser({
                      ...newUser,
                      phone_number: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Role

                <select
                  value={newUser.role}
                  onChange={(event) =>
                    setNewUser({
                      ...newUser,
                      role: event.target.value as UserRole,
                    })
                  }
                >
                  {allowedRoles.map((role) => (
                    <option
                      key={role}
                      value={role}
                    >
                      {roleLabels[role]}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Temporary password

                <input
                  type="password"
                  minLength={10}
                  required
                  value={newUser.password}
                  onChange={(event) =>
                    setNewUser({
                      ...newUser,
                      password: event.target.value,
                    })
                  }
                />
              </label>

              {userError && (
                <div className="alert alert-error">
                  {userError}
                </div>
              )}

              <button
                type="submit"
                className="button"
                disabled={createUser.isPending}
              >
                <Plus size={18} />

                {createUser.isPending
                  ? 'Creating…'
                  : 'Create user'}
              </button>
            </div>
          </form>

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Operational users</h2>

                <p>
                  Reserved founder identities appear only in
                  Governance.
                </p>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {userRows.map((adminUser) => (
                    <tr key={adminUser.id}>
                      <td>
                        <strong>
                          {adminUser.full_name}
                        </strong>
                      </td>

                      <td>
                        {adminUser.email}
                      </td>

                      <td>
                        {roleLabels[adminUser.role]}
                      </td>

                      <td>
                        {adminUser.is_active
                          ? 'Active'
                          : 'Disabled'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {section === 'volunteers' && (
        <>
          <section className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">
                  Applications awaiting review
                </span>

                <h2>
                  Pending volunteer applications
                </h2>

                <p>
                  Approving an application does not immediately make
                  the volunteer assignable. The volunteer must also
                  complete the safety acknowledgement and activate
                  their profile.
                </p>
              </div>

              <span>
                <Clock3 size={17} />
                {pendingVolunteerRows.length} pending
              </span>
            </div>

            {reviewError && (
              <div className="alert alert-error">
                {reviewError}
              </div>
            )}

            {pendingVolunteerRows.length === 0 ? (
              <div className="alert">
                There are no volunteer applications awaiting review.
              </div>
            ) : (
              <div className="card-list">
                {pendingVolunteerRows.map(
                  (volunteer) => {
                    const reviewingThisVolunteer =
                      reviewVolunteer.isPending
                      && reviewVolunteer.variables?.id
                        === volunteer.id

                    return (
                      <article key={volunteer.id}>
                        <div className="avatar">
                          {volunteer.user_name
                            .charAt(0)
                            .toUpperCase()}
                        </div>

                        <div>
                          <strong>
                            {volunteer.user_name}
                          </strong>

                          <small>
                            {volunteer.user_email}
                          </small>

                          <p>
                            Applied{' '}
                            {new Date(
                              volunteer.created_at,
                            ).toLocaleString()}
                          </p>

                          <p>
                            Service areas:{' '}
                            {volunteer.service_areas
                              || 'Not provided'}
                          </p>

                          <p>
                            Vehicle:{' '}
                            {volunteer.has_vehicle
                              ? volunteer.vehicle_description
                                || 'Available'
                              : 'Not provided'}
                          </p>

                          <p>
                            Capacity:{' '}
                            {volunteer.capacity_kg} kg
                          </p>

                          <label>
                            Review note

                            <textarea
                              value={
                                reviewNotes[
                                  volunteer.id
                                ] ?? ''
                              }
                              onChange={(event) =>
                                setReviewNotes({
                                  ...reviewNotes,
                                  [volunteer.id]:
                                    event.target.value,
                                })
                              }
                              placeholder={
                                'Optional for approval; required for rejection.'
                              }
                            />
                          </label>

                          <div>
                            <button
                              type="button"
                              className="button button-small"
                              disabled={
                                reviewingThisVolunteer
                              }
                              onClick={() =>
                                submitVolunteerReview(
                                  volunteer,
                                  'approved',
                                )
                              }
                            >
                              <CheckCircle2 size={16} />

                              {reviewingThisVolunteer
                                ? 'Saving…'
                                : 'Approve'}
                            </button>

                            <button
                              type="button"
                              className="button button-small button-ghost"
                              disabled={
                                reviewingThisVolunteer
                              }
                              onClick={() =>
                                submitVolunteerReview(
                                  volunteer,
                                  'rejected',
                                )
                              }
                            >
                              <XCircle size={16} />
                              Reject
                            </button>
                          </div>
                        </div>

                        <span>
                          {approvalLabels[
                            volunteer.approval_status
                          ]}
                        </span>
                      </article>
                    )
                  },
                )}
              </div>
            )}
          </section>

          <div className="admin-split">
            <form
              className="panel admin-form"
              onSubmit={(event: FormEvent) => {
                event.preventDefault()
                createVolunteer.mutate()
              }}
            >
              <div className="panel-head">
                <div>
                  <h2>Create volunteer profile</h2>

                  <p>
                    Use this only for volunteer accounts created by
                    an administrator. Public volunteer signup creates
                    a pending profile automatically.
                  </p>
                </div>
              </div>

              <div className="form-stack">
                <label>
                  Volunteer user

                  <select
                    required
                    value={newVolunteer.user}
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        user: event.target.value,
                      })
                    }
                  >
                    <option value="">
                      Select user
                    </option>

                    {availableVolunteerUsers.map(
                      (volunteerUser) => (
                        <option
                          key={volunteerUser.id}
                          value={volunteerUser.id}
                        >
                          {volunteerUser.full_name}
                          {' — '}
                          {volunteerUser.email}
                        </option>
                      ),
                    )}
                  </select>
                </label>

                <label>
                  Service areas

                  <input
                    value={newVolunteer.service_areas}
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        service_areas:
                          event.target.value,
                      })
                    }
                  />
                </label>

                <label className="check">
                  <input
                    type="checkbox"
                    checked={newVolunteer.has_vehicle}
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        has_vehicle:
                          event.target.checked,
                      })
                    }
                  />

                  <span>
                    Has access to a vehicle
                  </span>
                </label>

                <label>
                  Vehicle description

                  <input
                    value={
                      newVolunteer.vehicle_description
                    }
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        vehicle_description:
                          event.target.value,
                      })
                    }
                  />
                </label>

                <label>
                  Capacity (kg)

                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={newVolunteer.capacity_kg}
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        capacity_kg:
                          event.target.value,
                      })
                    }
                  />
                </label>

                <label>
                  Availability notes

                  <textarea
                    value={
                      newVolunteer.availability_notes
                    }
                    onChange={(event) =>
                      setNewVolunteer({
                        ...newVolunteer,
                        availability_notes:
                          event.target.value,
                      })
                    }
                  />
                </label>

                <div className="alert">
                  New profiles begin pending, inactive, and without a
                  completed safety acknowledgement.
                </div>

                {volunteerError && (
                  <div className="alert alert-error">
                    {volunteerError}
                  </div>
                )}

                <button
                  type="submit"
                  className="button"
                  disabled={
                    createVolunteer.isPending
                  }
                >
                  <Plus size={18} />

                  {createVolunteer.isPending
                    ? 'Creating…'
                    : 'Create pending profile'}
                </button>
              </div>
            </form>

            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Volunteer roster</h2>

                  <p>
                    Eligibility requires approval, activation, and a
                    completed safety acknowledgement.
                  </p>
                </div>
              </div>

              <div className="card-list">
                {volunteerRows.map(
                  (volunteer) => (
                    <article key={volunteer.id}>
                      <div className="avatar">
                        {volunteer.user_name
                          .charAt(0)
                          .toUpperCase()}
                      </div>

                      <div>
                        <strong>
                          {volunteer.user_name}
                        </strong>

                        <small>
                          {volunteer.user_email}
                        </small>

                        <p>
                          {volunteer.service_areas
                            || 'No service areas provided'}
                          {' · '}
                          {volunteer.has_vehicle
                            ? volunteer.vehicle_description
                              || 'Vehicle available'
                            : 'No vehicle'}
                        </p>

                        <p>
                          Approval:{' '}
                          {
                            approvalLabels[
                              volunteer.approval_status
                            ]
                          }
                        </p>

                        <p>
                          Reviewed by:{' '}
                          {volunteer.reviewed_by_name
                            || 'Not reviewed'}
                          {' · '}
                          {formatDate(
                            volunteer.reviewed_at,
                          )}
                        </p>

                        {volunteer.review_note && (
                          <p>
                            Review note:{' '}
                            {volunteer.review_note}
                          </p>
                        )}

                        <p>
                          Profile:{' '}
                          {volunteer.active
                            ? 'Active'
                            : 'Inactive'}
                          {' · '}
                          Safety:{' '}
                          {volunteer.safety_acknowledged
                            ? 'Acknowledged'
                            : 'Not acknowledged'}
                        </p>
                      </div>

                      <span>
                        {volunteer.can_receive_assignments ? (
                          <>
                            <ShieldCheck size={16} />
                            Eligible
                          </>
                        ) : (
                          'Not assignable'
                        )}
                      </span>
                    </article>
                  ),
                )}
              </div>
            </section>
          </div>
        </>
      )}

      {section === 'organizations' && (
        <div className="admin-split">
          <form
            className="panel admin-form"
            onSubmit={(event: FormEvent) => {
              event.preventDefault()
              createOrganization.mutate()
            }}
          >
            <div className="panel-head">
              <h2>Add organization</h2>
            </div>

            <div className="form-stack">
              <label>
                Name

                <input
                  required
                  value={newOrganization.name}
                  onChange={(event) =>
                    setNewOrganization({
                      ...newOrganization,
                      name: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Type

                <select
                  value={
                    newOrganization.organization_type
                  }
                  onChange={(event) =>
                    setNewOrganization({
                      ...newOrganization,
                      organization_type:
                        event.target.value,
                    })
                  }
                >
                  <option value="corporate">
                    Corporate office
                  </option>

                  <option value="school">
                    School
                  </option>

                  <option value="community">
                    Residential community
                  </option>

                  <option value="nonprofit">
                    Community organization
                  </option>
                </select>
              </label>

              <label>
                Contact email

                <input
                  type="email"
                  required
                  value={
                    newOrganization.contact_email
                  }
                  onChange={(event) =>
                    setNewOrganization({
                      ...newOrganization,
                      contact_email:
                        event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Contact phone

                <input
                  value={
                    newOrganization.contact_phone
                  }
                  onChange={(event) =>
                    setNewOrganization({
                      ...newOrganization,
                      contact_phone:
                        event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Address

                <textarea
                  value={
                    newOrganization.address
                  }
                  onChange={(event) =>
                    setNewOrganization({
                      ...newOrganization,
                      address: event.target.value,
                    })
                  }
                />
              </label>

              {organizationError && (
                <div className="alert alert-error">
                  {organizationError}
                </div>
              )}

              <button
                type="submit"
                className="button"
                disabled={
                  createOrganization.isPending
                }
              >
                <Plus size={18} />

                {createOrganization.isPending
                  ? 'Adding…'
                  : 'Add organization'}
              </button>
            </div>
          </form>

          <section className="panel">
            <div className="panel-head">
              <h2>Organizations</h2>
            </div>

            <div className="card-list">
              {organizationRows.map(
                (organization) => (
                  <article key={organization.id}>
                    <div className="org-icon">
                      <Building2 />
                    </div>

                    <div>
                      <strong>
                        {organization.name}
                      </strong>

                      <small>
                        {organization.contact_email}
                      </small>

                      <p>
                        {organization.organization_type.replaceAll(
                          '_',
                          ' ',
                        )}
                        {' · '}
                        {organization.address
                          || 'Dubai'}
                      </p>
                    </div>

                    {organization.approved ? (
                      <span>Approved</span>
                    ) : (
                      <button
                        type="button"
                        className="button button-small button-ghost"
                        disabled={
                          approveOrganization.isPending
                        }
                        onClick={() =>
                          approveOrganization.mutate(
                            organization.id,
                          )
                        }
                      >
                        Approve
                      </button>
                    )}
                  </article>
                ),
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}