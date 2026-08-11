import { useState, useEffect } from 'react';
import { Routes, Route, NavLink, useLocation, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Sales from './pages/Sales';
import Purchases from './pages/Purchases';
import Inventory from './pages/Inventory';
import Accounting from './pages/Accounting';
import MasterData from './pages/MasterData';
import Partners from './pages/MasterData/Partners';
import HR from './pages/HR';
import LeaveRequests from './pages/HR/LeaveRequests';
import Projects from './pages/Projects';
import Manufacturing from './pages/Manufacturing';
import Reports from './pages/Reports';
import Payments from './pages/Payments';
import Currencies from './pages/Currencies';
import StockTakes from './pages/Inventory/StockTakes';
import SuperAdmin from './pages/SuperAdmin';
import CompanySettings from './pages/CompanySettings';
import { getMe, logout } from './api/client';
import './index.css';

const NAV = [
  { section: 'Main', items: [
    { to: '/', label: 'Dashboard', icon: '📊', end: true },
    { to: '/pos', label: 'Point of Sale', icon: '🛒' },
  ]},
  { section: 'Operations', items: [
    { to: '/sales', label: 'Sales', icon: '💰' },
    { to: '/purchases', label: 'Purchases', icon: '📦' },
    { to: '/inventory', label: 'Inventory', icon: '🏪' },
    { to: '/stock-takes', label: 'Stock Takes', icon: '🔍' },
    { to: '/manufacturing', label: 'Manufacturing', icon: '🏭' },
    { to: '/projects', label: 'Projects', icon: '📐' },
  ]},
  { section: 'Finance', items: [
   { to: '/accounting', label: 'Accounting', icon: '📒' },
   { to: '/payments', label: 'Payments', icon: '💳' },
   { to: '/reports', label: 'Reports', icon: '📊' },
   { to: '/currencies', label: 'Currencies & Rates', icon: '💱' },
  ]},
  { section: 'Master Data', items: [
   { to: '/items', label: 'Items & Products', icon: '🏷️' },
   { to: '/partners', label: 'Partners', icon: '🤝' },
  ]},
];

const SUPERADMIN_NAV = [
  { section: 'System Administration', items: [
    { to: '/superadmin', label: 'Super Admin', icon: '⚙️' },
  ]},
];

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const [currentUser, setCurrentUser] = useState(null);
  const location = useLocation();

  const handleLogin = async () => {
    try {
      const me = await getMe();
      setCurrentUser(me.data);
    } catch { }
    setIsLoggedIn(true);
  };

  useEffect(() => {
    if (isLoggedIn) {
      getMe().then(r => setCurrentUser(r.data)).catch(() => {});
    }
  }, [isLoggedIn]);

  const handleLogout = async () => {
    try { await logout(); } catch { /* session already expired */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('company_id');
    localStorage.removeItem('branch_id');
    setCurrentUser(null);
    setIsLoggedIn(false);
  };

  const getTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/pos') return 'Point of Sale';
    if (path === '/payments') return 'Payments';
    if (path === '/sales') return 'Sales Invoices';
    if (path === '/purchases') return 'Purchase Invoices';
    if (path === '/inventory') return 'Inventory Management';
    if (path === '/stock-takes') return 'Stock Takes';
    if (path === '/manufacturing') return 'Manufacturing';
    if (path === '/accounting') return 'Accounting & Finance';
    if (path === '/reports') return 'Reports';
    if (path === '/currencies') return 'Currencies & Exchange Rates';
    if (path === '/items') return 'Items & Products';
    if (path === '/partners') return 'Customers & Suppliers';
    if (path === '/hr') return 'Human Resources';
    if (path === '/leave-requests') return 'Leave Requests';
    if (path === '/projects') return 'Projects & Contracting';
    if (path === '/superadmin') return 'Super Admin Dashboard';
    if (path === '/company-settings') return 'Company Settings';
    return 'ERP System';
  };

  const isSuperUser = currentUser?.is_superuser === true;

  if (!isLoggedIn) return <Login onLogin={handleLogin} />;

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">⚡ ERP Pro</div>
        {NAV.map(section => (
          <div key={section.section}>
            <div className="nav-section-title">{section.section}</div>
            <nav className="nav-menu">
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
        {/* Company settings link for all users */}
        <div>
          <div className="nav-section-title">Settings</div>
          <nav className="nav-menu">
            <NavLink to="/company-settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">🏢</span> Company Settings
            </NavLink>
          </nav>
        </div>
        {/* SuperAdmin only */}
        {isSuperUser && SUPERADMIN_NAV.map(section => (
          <div key={section.section}>
            <div className="nav-section-title">{section.section}</div>
            <nav className="nav-menu">
              {section.items.map(item => (
                <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
        <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
          {currentUser && (
            <div style={{ padding: '0.5rem 0.875rem', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              👤 {currentUser.full_name || currentUser.email}
              {isSuperUser && <span style={{ marginLeft: '0.5rem', color: 'var(--primary-color)', fontWeight: 600 }}>[SA]</span>}
            </div>
          )}
          <button className="nav-item" onClick={handleLogout} style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}>
            <span className="nav-icon">🚪</span> Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <h1 className="page-title">{getTitle()}</h1>
        </header>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pos" element={<POS />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/sales" element={<Sales />} />
          <Route path="/purchases" element={<Purchases />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/stock-takes" element={<StockTakes />} />
          <Route path="/manufacturing" element={<Manufacturing />} />
          <Route path="/accounting" element={<Accounting />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/currencies" element={<Currencies />} />
          <Route path="/items" element={<MasterData />} />
          <Route path="/partners" element={<Partners />} />
          <Route path="/hr" element={<HR />} />
          <Route path="/leave-requests" element={<LeaveRequests />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/company-settings" element={<CompanySettings />} />
          {/* SuperAdmin routes: redirect non-superusers to home */}
          <Route path="/superadmin" element={isSuperUser ? <SuperAdmin /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
