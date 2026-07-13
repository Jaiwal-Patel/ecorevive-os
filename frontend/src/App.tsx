import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AccountPage } from './pages/AccountPage'
import { AdministrationPage } from './pages/AdministrationPage'
import { FulfillmentPage } from './pages/FulfillmentPage'
import { DashboardPage } from './pages/DashboardPage'
import { GovernancePage } from './pages/GovernancePage'
import { HomePage } from './pages/HomePage'
import { ImpactAdminPage } from './pages/ImpactAdminPage'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import { NewRequestPage } from './pages/NewRequestPage'
import { OperationsPage } from './pages/OperationsPage'
import { RequestDetailPage } from './pages/RequestDetailPage'
import { RequestsPage } from './pages/RequestsPage'

const adminRoles = ['founder_guardian','principal_admin','operations_admin'] as const
const governanceRoles = ['founder_guardian','founder_recovery','principal_admin'] as const

export default function App(){return <Routes><Route path="/" element={<HomePage/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/><Route element={<ProtectedRoute/>}><Route element={<AppShell/>}><Route path="/dashboard" element={<DashboardPage/>}/><Route path="/account" element={<AccountPage/>}/><Route path="/requests" element={<RequestsPage/>}/><Route path="/requests/new" element={<NewRequestPage/>}/><Route path="/requests/:id" element={<RequestDetailPage/>}/><Route element={<ProtectedRoute roles={[...adminRoles]}/>}><Route path="/operations" element={<OperationsPage/>}/><Route path="/fulfillment" element={<FulfillmentPage/>}/><Route path="/administration" element={<AdministrationPage/>}/><Route path="/impact-admin" element={<ImpactAdminPage/>}/></Route><Route element={<ProtectedRoute roles={[...governanceRoles]}/>}><Route path="/governance" element={<GovernancePage/>}/></Route></Route></Route><Route path="*" element={<HomePage/>}/></Routes>}
