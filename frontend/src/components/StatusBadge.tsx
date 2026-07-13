const labels: Record<string, string> = {
  draft: 'Draft', submitted: 'Submitted', under_review: 'Under review', approved: 'Approved',
  scheduled: 'Scheduled', assigned: 'Assigned', collected: 'Collected',
  handed_to_recycler: 'Recycler handover', completed: 'Completed', cancelled: 'Cancelled',
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{labels[status] ?? status}</span>
}
