import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from '../src/components/StatusBadge'

describe('StatusBadge',()=>{it('renders a readable label',()=>{render(<StatusBadge status="handed_to_recycler"/>);expect(screen.getByText('Recycler handover')).toBeInTheDocument()})})
