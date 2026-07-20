import { Minus, Plus, Send } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from 'react'
import { useNavigate } from 'react-router-dom'

import { api, errorMessage } from '../api/client'
import type { ItemCategory } from '../types'

type DraftItem = {
  category: string
  description: string
  quantity: number
  condition: string
  approximate_weight_kg: string
}

type RequestForm = {
  address_line: string
  area: string
  city: string
  preferred_date: string
  preferred_time_window: string
  access_instructions: string
  resident_notes: string
  estimated_weight_kg: string
  consent_to_contact: boolean
  consent_to_data_processing: boolean
}

type ItemErrors = {
  category?: string
  description?: string
  quantity?: string
  condition?: string
  approximate_weight_kg?: string
}

type FormErrors = {
  address_line?: string
  area?: string
  city?: string
  preferred_date?: string
  preferred_time_window?: string
  access_instructions?: string
  consent_to_contact?: string
  consent_to_data_processing?: string
  items: ItemErrors[]
}

const blankItem = (): DraftItem => ({
  category: '',
  description: '',
  quantity: 1,
  condition: '',
  approximate_weight_kg: '',
})

const initialForm: RequestForm = {
  address_line: '',
  area: '',
  city: 'Dubai',
  preferred_date: '',
  preferred_time_window: '',
  access_instructions: '',
  resident_notes: '',
  estimated_weight_kg: '',
  consent_to_contact: true,
  consent_to_data_processing: false,
}

const isBlank = (value: string) => value.trim().length === 0

export function NewRequestPage() {
  const navigate = useNavigate()
  const formRef = useRef<HTMLFormElement>(null)

  const { data: categories = [] } = useQuery<ItemCategory[]>({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await api.get<ItemCategory[]>(
        '/item-categories/',
      )

      return response.data
    },
  })

  const [form, setForm] = useState<RequestForm>(initialForm)
  const [items, setItems] = useState<DraftItem[]>([blankItem()])
  const [submissionAttempted, setSubmissionAttempted] =
    useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const updateForm = <Key extends keyof RequestForm>(
    key: Key,
    value: RequestForm[Key],
  ) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }))
  }

  const updateItem = (
    index: number,
    patch: Partial<DraftItem>,
  ) => {
    setItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              ...patch,
            }
          : item,
      ),
    )
  }

  const addItem = () => {
    setItems((current) => [...current, blankItem()])
  }

  const removeItem = (index: number) => {
    setItems((current) =>
      current.filter((_, itemIndex) => itemIndex !== index),
    )
  }

  const validationErrors = useMemo<FormErrors>(() => {
    const errors: FormErrors = {
      items: items.map(() => ({})),
    }

    if (isBlank(form.address_line)) {
      errors.address_line = 'Address is required.'
    }

    if (isBlank(form.area)) {
      errors.area = 'Area is required.'
    }

    if (isBlank(form.city)) {
      errors.city = 'City is required.'
    }

    if (isBlank(form.preferred_date)) {
      errors.preferred_date = 'Preferred date is required.'
    }

    if (isBlank(form.preferred_time_window)) {
      errors.preferred_time_window =
        'Preferred time window is required.'
    }

    if (isBlank(form.access_instructions)) {
      errors.access_instructions =
        'Access instructions are required.'
    }

    if (!form.consent_to_contact) {
      errors.consent_to_contact =
        'You must allow EcoRevive to contact you about the request.'
    }

    if (!form.consent_to_data_processing) {
      errors.consent_to_data_processing =
        'You must consent to data processing.'
    }

    items.forEach((item, index) => {
      const itemErrors: ItemErrors = {}

      if (isBlank(item.category)) {
        itemErrors.category = 'Category is required.'
      }

      if (isBlank(item.description)) {
        itemErrors.description = 'Description is required.'
      }

      if (
        !Number.isFinite(item.quantity) ||
        item.quantity < 1
      ) {
        itemErrors.quantity =
          'Quantity must be at least 1.'
      }

      if (isBlank(item.condition)) {
        itemErrors.condition = 'Condition is required.'
      }

      if (isBlank(item.approximate_weight_kg)) {
        itemErrors.approximate_weight_kg =
          'Approximate weight is required.'
      } else {
        const weight = Number(item.approximate_weight_kg)

        if (!Number.isFinite(weight) || weight <= 0) {
          itemErrors.approximate_weight_kg =
            'Weight must be greater than 0.'
        }
      }

      errors.items[index] = itemErrors
    })

    return errors
  }, [form, items])

  const hasValidationErrors = useMemo(() => {
    const hasFormErrors = Boolean(
      validationErrors.address_line ||
        validationErrors.area ||
        validationErrors.city ||
        validationErrors.preferred_date ||
        validationErrors.preferred_time_window ||
        validationErrors.access_instructions ||
        validationErrors.consent_to_contact ||
        validationErrors.consent_to_data_processing,
    )

    const hasItemErrors = validationErrors.items.some(
      (itemError) =>
        Object.values(itemError).some(Boolean),
    )

    return hasFormErrors || hasItemErrors
  }, [validationErrors])

  const invalidClass = (
    message: string | undefined,
  ): string =>
    submissionAttempted && message
      ? 'request-field-invalid'
      : ''

  const displayError = (
    message: string | undefined,
  ) =>
    submissionAttempted && message ? (
      <small className="request-field-error">
        {message}
      </small>
    ) : null

  const focusFirstInvalidField = () => {
    window.requestAnimationFrame(() => {
      const firstInvalid =
        formRef.current?.querySelector<
          HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
        >('.request-field-invalid')

      firstInvalid?.focus()
      firstInvalid?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    })
  }

  const submit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    setSubmissionAttempted(true)
    setError('')

    if (hasValidationErrors) {
      setError(
        'Please complete every required field highlighted below.',
      )
      focusFirstInvalidField()
      return
    }

    setBusy(true)

    try {
      const payload = {
        ...form,
        address_line: form.address_line.trim(),
        area: form.area.trim(),
        city: form.city.trim(),
        preferred_time_window:
          form.preferred_time_window.trim(),
        access_instructions:
          form.access_instructions.trim(),
        resident_notes: form.resident_notes.trim(),
        preferred_date: form.preferred_date,
        estimated_weight_kg:
          form.estimated_weight_kg || null,
        items: items.map((item) => ({
          category: item.category,
          description: item.description.trim(),
          quantity: item.quantity,
          condition: item.condition.trim(),
          approximate_weight_kg:
            item.approximate_weight_kg,
        })),
      }

      const response = await api.post(
        '/collection-requests/',
        payload,
      )

      await api.post(
        `/collection-requests/${response.data.id}/submit/`,
        {},
      )

      navigate(`/requests/${response.data.id}`)
    } catch (submissionError) {
      setError(errorMessage(submissionError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="workspace collection-request-workspace">
      <style>{`
        .collection-request-workspace {
          width: 100%;
          max-width: 1320px;
        }

        .item-row.collection-request-item-row {
          display: grid;
          grid-template-columns:
            minmax(210px, 1.2fr)
            minmax(245px, 1.4fr)
            minmax(90px, 0.5fr)
            minmax(155px, 0.85fr)
            minmax(110px, 0.6fr)
            38px;
          gap: 12px;
          align-items: end;
          width: 100%;
        }

        .collection-request-item-row > label {
          min-width: 0;
        }

        .collection-request-item-row input,
        .collection-request-item-row select {
          display: block;
          width: 100%;
          min-width: 0;
          height: 44px;
        }

        .required-label::after {
          content: ' *';
          color: #a43e3e;
        }

        .request-field-invalid {
          border-color: #b42318 !important;
          background: #fff7f6 !important;
          box-shadow: 0 0 0 3px rgba(180, 35, 24, 0.12) !important;
        }

        .request-field-error {
          display: block;
          margin-top: 2px;
          color: #a43e3e;
          font-size: 0.76rem;
          font-weight: 600;
          line-height: 1.35;
        }

        .request-checkbox-invalid {
          padding: 10px 12px;
          border: 1px solid #b42318;
          border-radius: 10px;
          background: #fff7f6;
        }

        .request-checkbox-invalid input {
          outline: 2px solid rgba(180, 35, 24, 0.25);
          outline-offset: 2px;
        }

        .request-validation-summary {
          margin: 20px 30px 0;
        }

        @media (max-width: 1250px) {
          .item-row.collection-request-item-row {
            grid-template-columns:
              minmax(220px, 1fr)
              minmax(220px, 1fr)
              minmax(90px, 0.45fr);
          }

          .collection-request-item-row
            > label:nth-of-type(4) {
            grid-column: 1;
            grid-row: 2;
          }

          .collection-request-item-row
            > label:nth-of-type(5) {
            grid-column: 2;
            grid-row: 2;
          }

          .collection-request-item-row > button {
            grid-column: 3;
            grid-row: 2;
          }
        }

        @media (max-width: 700px) {
          .collection-request-workspace {
            max-width: none;
          }

          .item-row.collection-request-item-row {
            grid-template-columns: minmax(0, 1fr);
          }

          .collection-request-item-row > label,
          .collection-request-item-row
            > label:nth-of-type(4),
          .collection-request-item-row
            > label:nth-of-type(5),
          .collection-request-item-row > button {
            grid-column: 1;
            grid-row: auto;
          }

          .collection-request-item-row > button {
            justify-self: end;
          }

          .request-validation-summary {
            margin-left: 20px;
            margin-right: 20px;
          }
        }
      `}</style>

      <div className="page-head">
        <div>
          <span className="eyebrow">
            Household or organization pickup
          </span>

          <h1>Request a collection</h1>

          <p>
            Tell the operations team what needs collecting and
            when access is easiest.
          </p>
        </div>
      </div>

      <form
        ref={formRef}
        className="panel form-sections"
        onSubmit={submit}
        noValidate
      >
        <section>
          <div className="form-section-head">
            <span>1</span>

            <div>
              <h2>Pickup location</h2>

              <p>
                Exact addresses remain private to authorized
                operations staff.
              </p>
            </div>
          </div>

          <div className="form-grid">
            <label className="span-2">
              <span className="required-label">
                Address
              </span>

              <input
                className={invalidClass(
                  validationErrors.address_line,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.address_line,
                )}
                value={form.address_line}
                placeholder="Building, apartment/villa and street"
                onChange={(event) =>
                  updateForm(
                    'address_line',
                    event.target.value,
                  )
                }
              />

              {displayError(
                validationErrors.address_line,
              )}
            </label>

            <label>
              <span className="required-label">
                Area
              </span>

              <input
                className={invalidClass(
                  validationErrors.area,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.area,
                )}
                value={form.area}
                placeholder="The Greens"
                onChange={(event) =>
                  updateForm('area', event.target.value)
                }
              />

              {displayError(validationErrors.area)}
            </label>

            <label>
              <span className="required-label">
                City
              </span>

              <input
                className={invalidClass(
                  validationErrors.city,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.city,
                )}
                value={form.city}
                onChange={(event) =>
                  updateForm('city', event.target.value)
                }
              />

              {displayError(validationErrors.city)}
            </label>
          </div>
        </section>

        <section>
          <div className="form-section-head">
            <span>2</span>

            <div>
              <h2>E-waste items</h2>

              <p>
                Add each type of device separately for better
                planning.
              </p>
            </div>
          </div>

          <div className="item-editor">
            {items.map((item, index) => {
              const itemErrors =
                validationErrors.items[index] ?? {}

              return (
                <div
                  className={
                    'item-row collection-request-item-row'
                  }
                  key={index}
                >
                  <label>
                    <span className="required-label">
                      Category
                    </span>

                    <select
                      className={invalidClass(
                        itemErrors.category,
                      )}
                      aria-invalid={Boolean(
                        submissionAttempted &&
                          itemErrors.category,
                      )}
                      value={item.category}
                      onChange={(event) =>
                        updateItem(index, {
                          category: event.target.value,
                        })
                      }
                    >
                      <option value="">
                        Select category
                      </option>

                      {categories.map((category) => (
                        <option
                          key={category.id}
                          value={String(category.id)}
                        >
                          {category.name}
                        </option>
                      ))}
                    </select>

                    {displayError(itemErrors.category)}
                  </label>

                  <label className="item-description">
                    <span className="required-label">
                      Description
                    </span>

                    <input
                      className={invalidClass(
                        itemErrors.description,
                      )}
                      aria-invalid={Boolean(
                        submissionAttempted &&
                          itemErrors.description,
                      )}
                      value={item.description}
                      placeholder="e.g. 55-inch television"
                      onChange={(event) =>
                        updateItem(index, {
                          description: event.target.value,
                        })
                      }
                    />

                    {displayError(
                      itemErrors.description,
                    )}
                  </label>

                  <label>
                    <span className="required-label">
                      Quantity
                    </span>

                    <input
                      className={invalidClass(
                        itemErrors.quantity,
                      )}
                      aria-invalid={Boolean(
                        submissionAttempted &&
                          itemErrors.quantity,
                      )}
                      type="number"
                      min="1"
                      step="1"
                      value={item.quantity}
                      onChange={(event) =>
                        updateItem(index, {
                          quantity: Number(
                            event.target.value,
                          ),
                        })
                      }
                    />

                    {displayError(itemErrors.quantity)}
                  </label>

                  <label>
                    <span className="required-label">
                      Condition
                    </span>

                    <input
                      className={invalidClass(
                        itemErrors.condition,
                      )}
                      aria-invalid={Boolean(
                        submissionAttempted &&
                          itemErrors.condition,
                      )}
                      value={item.condition}
                      placeholder="Working / faulty"
                      onChange={(event) =>
                        updateItem(index, {
                          condition: event.target.value,
                        })
                      }
                    />

                    {displayError(itemErrors.condition)}
                  </label>

                  <label>
                    <span className="required-label">
                      Approx. kg
                    </span>

                    <input
                      className={invalidClass(
                        itemErrors.approximate_weight_kg,
                      )}
                      aria-invalid={Boolean(
                        submissionAttempted &&
                          itemErrors.approximate_weight_kg,
                      )}
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={item.approximate_weight_kg}
                      onChange={(event) =>
                        updateItem(index, {
                          approximate_weight_kg:
                            event.target.value,
                        })
                      }
                    />

                    {displayError(
                      itemErrors.approximate_weight_kg,
                    )}
                  </label>

                  <button
                    type="button"
                    className="icon-button danger"
                    aria-label={`Remove item ${index + 1}`}
                    disabled={items.length === 1}
                    onClick={() => removeItem(index)}
                  >
                    <Minus size={18} />
                  </button>
                </div>
              )
            })}
          </div>

          <button
            type="button"
            className="text-button"
            onClick={addItem}
          >
            <Plus size={17} />
            Add another item
          </button>
        </section>

        <section>
          <div className="form-section-head">
            <span>3</span>

            <div>
              <h2>Timing and access</h2>

              <p>
                The team will confirm the final pickup schedule.
              </p>
            </div>
          </div>

          <div className="form-grid">
            <label>
              <span className="required-label">
                Preferred date
              </span>

              <input
                className={invalidClass(
                  validationErrors.preferred_date,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.preferred_date,
                )}
                type="date"
                value={form.preferred_date}
                onChange={(event) =>
                  updateForm(
                    'preferred_date',
                    event.target.value,
                  )
                }
              />

              {displayError(
                validationErrors.preferred_date,
              )}
            </label>

            <label>
              <span className="required-label">
                Time window
              </span>

              <input
                className={invalidClass(
                  validationErrors.preferred_time_window,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.preferred_time_window,
                )}
                value={form.preferred_time_window}
                placeholder="e.g. Saturday 10am–1pm"
                onChange={(event) =>
                  updateForm(
                    'preferred_time_window',
                    event.target.value,
                  )
                }
              />

              {displayError(
                validationErrors.preferred_time_window,
              )}
            </label>

            <label className="span-2">
              <span className="required-label">
                Access instructions
              </span>

              <textarea
                className={invalidClass(
                  validationErrors.access_instructions,
                )}
                aria-invalid={Boolean(
                  submissionAttempted &&
                    validationErrors.access_instructions,
                )}
                value={form.access_instructions}
                placeholder="Parking, security or gate details"
                onChange={(event) =>
                  updateForm(
                    'access_instructions',
                    event.target.value,
                  )
                }
              />

              {displayError(
                validationErrors.access_instructions,
              )}
            </label>

            <label className="span-2">
              Additional notes

              <textarea
                value={form.resident_notes}
                placeholder="Optional"
                onChange={(event) =>
                  updateForm(
                    'resident_notes',
                    event.target.value,
                  )
                }
              />
            </label>
          </div>
        </section>

        <section>
          <div className="form-section-head">
            <span>4</span>

            <div>
              <h2>Consent</h2>

              <p>
                EcoRevive uses this information only to
                coordinate and verify the collection.
              </p>
            </div>
          </div>

          <label
            className={`check ${
              submissionAttempted &&
              validationErrors.consent_to_contact
                ? 'request-checkbox-invalid'
                : ''
            }`}
          >
            <input
              type="checkbox"
              checked={form.consent_to_contact}
              onChange={(event) =>
                updateForm(
                  'consent_to_contact',
                  event.target.checked,
                )
              }
            />

            <span>
              EcoRevive may contact me by email or
              phone/WhatsApp about this request.
              <span className="required-label" />

              {displayError(
                validationErrors.consent_to_contact,
              )}
            </span>
          </label>

          <label
            className={`check ${
              submissionAttempted &&
              validationErrors.consent_to_data_processing
                ? 'request-checkbox-invalid'
                : ''
            }`}
          >
            <input
              type="checkbox"
              checked={form.consent_to_data_processing}
              onChange={(event) =>
                updateForm(
                  'consent_to_data_processing',
                  event.target.checked,
                )
              }
            />

            <span>
              I consent to processing the submitted
              information for collection coordination.
              <span className="required-label" />

              {displayError(
                validationErrors.consent_to_data_processing,
              )}
            </span>
          </label>
        </section>

        {error && (
          <div className="alert alert-error request-validation-summary">
            {error}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            className="button"
            disabled={busy}
          >
            <Send size={18} />

            {busy
              ? 'Submitting…'
              : 'Submit collection request'}
          </button>
        </div>
      </form>
    </div>
  )
}