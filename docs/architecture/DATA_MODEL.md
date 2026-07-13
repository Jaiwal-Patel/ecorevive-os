# Data Model

## Core traceability chain

```text
User → CollectionRequest → CollectionItem
                    ↓
             PickupAssignment → VolunteerProfile
                    ↓
              HandoverRequest → HandoverBatch
                    ↓
             verified weight and public impact
```

## Identity

`User` uses email as the login identifier and contains a single operational role. Reserved governance roles are protected at the model and API layers.

## Collection workflow

A `CollectionRequest` contains one or more `CollectionItem` rows. Every status change creates a `StatusTransition`. The allowed state machine is:

```text
Draft → Submitted → Under review → Approved → Scheduled
      → Assigned → Collected → Handed to recycler → Completed
```

Cancellation is allowed only before a recycler handover.

## Logistics

`RoutePlan` contains ordered `RouteStop` rows. A request can appear in multiple historical plans, but only once within a given plan.

## Impact

`ImpactMetric` is intentionally editable data, not hard-coded copy. The public homepage reads current verified values from the API.
