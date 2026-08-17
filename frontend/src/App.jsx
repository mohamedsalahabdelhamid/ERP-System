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
import Roles from './pages/Roles';
import { getMe, logout } from './api/client';
import { useTranslation } from './contexts/TranslationContext';
import './index.css';

const getNavConfig = (t) => [
  { section: 'Main', items: [
    { to: '/', label: t('common.dashboard'), icon: '📊', end: true },
    { to: '/pos', label: t('common.pos'), icon: '🛒' },
  ]},
  { section: 'Operations', items: [
    { to: '/sales', label: t('common.sales'), icon: '💰' },
    { to: '/purchases', label: t('common.purchases'), icon: '📦' },
    { to: '/inventory', label: t('common.inventory'), icon: '🏪' },
    { to: '/stock-takes', label: t('common.stock_takes'), icon: '🔍' },
    { to: '/manufacturing', label: t('common.manufacturing'), icon: '🏭' },
    { to: '/projects', label: t('common.projects'), icon: '📐' },
  ]},
  { section: 'Finance', items: [
   { to: '/accounting', label: t('common.accounting'), icon: '📒' },
   { to: '/payments', label: t('common.payments'), icon: '💳' },
   { to: '/reports', label: t('common.reports'), icon: '📊' },
   { to: '/currencies', label: t('common.currencies'), icon: '💱' },
  ]},
  { section: 'HR', items: [
   { to: '/hr', label: t('common.hr'), icon: '👥' },
   { to: '/leave-requests', label: t('common.leave_requests'), icon: '📅' },
  ]},
  { section: 'Master Data', items: [
   { to: '/items', label: t('common.items_products'), icon: '🏷️' },
   { to: '/partners', label: t('common.partners'), icon: '🤝' },
  ]},
];

const getSuperAdminNavConfig = (t) => [
  { section: 'System Administration', items: [
    { to: '/superadmin', label: t('common.superadmin'), icon: '⚙️' },
  ]},
];

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const [currentUser, setCurrentUser] = useState(null);
  const location = useLocation();
  const { t, language, toggleLanguage } = useTranslation();
  const [theme, setTheme] = useState(localStorage.getItem('erp_theme') || 'dark');

  useEffect(() => {
    localStorage.setItem('erp_theme', theme);
    if (theme === 'light') {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
  }, [theme]);

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
    if (path === '/') return t('common.dashboard');
    if (path === '/pos') return t('common.pos');
    if (path === '/payments') return t('common.payments');
    if (path === '/sales') return t('common.sales');
    if (path === '/purchases') return t('common.purchases');
    if (path === '/inventory') return t('common.inventory');
    if (path === '/stock-takes') return t('common.stock_takes');
    if (path === '/manufacturing') return t('common.manufacturing');
    if (path === '/accounting') return t('common.accounting');
    if (path === '/reports') return t('common.reports');
    if (path === '/currencies') return t('common.currencies');
    if (path === '/items') return t('common.items_products');
    if (path === '/partners') return t('common.partners');
    if (path === '/hr') return t('common.hr');
    if (path === '/leave-requests') return t('common.leave_requests');
    if (path === '/projects') return t('common.projects');
    if (path === '/superadmin') return t('common.superadmin');
    if (path === '/company-settings') return t('common.settings');
    if (path === '/roles') return t('common.roles');
    return 'ERP System';
  };

  const isSuperUser = currentUser?.is_superuser === true;
  const hasRolesPermission = currentUser?.permissions?.includes('roles.manage');

  if (!isLoggedIn) return <Login onLogin={handleLogin} />;

  const NAV = getNavConfig(t);
  const SUPERADMIN_NAV = getSuperAdminNavConfig(t);

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
          <div className="nav-section-title">{t('common.settings')}</div>
          <nav className="nav-menu">
            <NavLink to="/company-settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">🏢</span> {t('common.settings')}
            </NavLink>
            {hasRolesPermission && (
              <NavLink to="/roles" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                <span className="nav-icon">🔐</span> {t('common.roles')}
              </NavLink>
            )}
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
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', padding: '0 0.5rem' }}>
            <button 
              onClick={toggleLanguage} 
              className="tab-btn" 
              style={{ flex: 1, padding: '0.25rem' }}
            >
              🌐 {t('lang.switch')}
            </button>
            <button 
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} 
              className="tab-btn" 
              style={{ flex: 1, padding: '0.25rem' }}
            >
              {theme === 'dark' ? '☀️ ' + t('theme.light') : '🌙 ' + t('theme.dark')}
            </button>
          </div>
          {currentUser && (
            <div style={{ padding: '0.5rem 0.875rem', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              👤 {currentUser.full_name || currentUser.email}
              {isSuperUser && <span style={{ marginLeft: '0.5rem', color: 'var(--primary-color)', fontWeight: 600 }}>[SA]</span>}
            </div>
          )}
          <button className="nav-item" onClick={handleLogout} style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}>
            <span className="nav-icon">🚪</span> {t('common.logout')}
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
          <Route path="/roles" element={<Roles />} />
          {/* SuperAdmin routes: redirect non-superusers to home */}
          <Route path="/superadmin" element={isSuperUser ? <SuperAdmin /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

