export type UserRole =
  | 'founder_guardian'
  | 'founder_recovery'
  | 'principal_admin'
  | 'operations_admin'
  | 'volunteer'
  | 'corporate_coordinator'
  | 'resident'

export type VolunteerApprovalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'

export interface User {
  id: string
  email: string
  full_name: string
  phone_number: string
  role: UserRole
  must_change_password: boolean
  date_joined: string
}

export interface PublicConfig {
  project_name: string
  organization_name: string
  tagline: string
  service_city: string
  service_country: string
  public_site_url: string
}

export interface ImpactMetric {
  id: string
  key: string
  label: string
  value: string
  unit: string
  description: string
  public: boolean
  display_order: number
  updated_at: string
}

export interface ItemCategory {
  id: string
  name: string
  slug: string
  description: string
  active: boolean
}

export interface CollectionItem {
  id?: string
  category: string
  category_name?: string
  description: string
  quantity: number
  condition: string
  approximate_weight_kg: string | null
  photo?: string | null
}

export interface StatusTransition {
  id: string
  from_status: string
  to_status: string
  actor_name: string
  note: string
  created_at: string
}

export interface CollectionRequest {
  id: string
  public_reference: string
  requester_name: string
  requester_email: string
  organization: string | null
  status: string
  status_label: string
  address_line: string
  area: string
  city: string
  latitude: string | null
  longitude: string | null
  preferred_date: string | null
  preferred_time_window: string
  access_instructions: string
  resident_notes: string
  estimated_weight_kg: string | null
  actual_weight_kg: string | null
  consent_to_contact: boolean
  consent_to_data_processing: boolean
  submitted_at: string | null
  completed_at: string | null
  items: CollectionItem[]
  status_history: StatusTransition[]
  created_at: string
  updated_at: string
}

export interface GovernanceIdentity {
  id: string
  email: string
  full_name: string
  role: UserRole
  role_label: string
  is_active: boolean
  date_joined: string
  updated_at: string
}

export interface AuditEvent {
  id: string
  actor_email: string | null
  event_type: string
  summary: string
  object_type: string
  object_id: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AdminUser {
  id: string
  email: string
  full_name: string
  phone_number: string
  role: UserRole
  is_active: boolean
  date_joined: string
}

export interface VolunteerProfile {
  id: string
  user: string
  user_email: string
  user_name: string

  approval_status: VolunteerApprovalStatus
  approval_status_label: string

  reviewed_by: string | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  review_note: string

  service_areas: string
  has_vehicle: boolean
  vehicle_description: string
  capacity_kg: string
  availability_notes: string

  active: boolean
  safety_acknowledged: boolean
  is_approved: boolean
  can_receive_assignments: boolean

  created_at: string
  updated_at: string
}

export interface Organization {
  id: string
  name: string
  organization_type: string
  contact_email: string
  contact_phone: string
  address: string
  approved: boolean
  created_by_email: string
  created_at: string
}

export interface PickupAssignment {
  id: string
  request: string
  request_reference: string
  volunteer: string
  volunteer_name: string
  scheduled_for: string
  status: string
  instructions: string
  assigned_by: string
  created_at: string
}

export interface HandoverRequestSummary {
  request: string
  request_reference: string
  verified_weight_kg: string
}

export interface HandoverBatch {
  id: string
  reference: string
  recycler_name: string
  handover_date: string
  receipt_number: string
  total_weight_kg: string
  included_requests: HandoverRequestSummary[]
  recorded_by: string
  created_at: string
}