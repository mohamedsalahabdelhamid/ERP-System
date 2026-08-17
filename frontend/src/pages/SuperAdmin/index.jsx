import { useState, useEffect } from 'react';
import { getPlatformModules, getPlatformCompanies, createPlatformCompany, updatePlatformCompany, getPlatformCompanyUsers, createPlatformCompanyUser, resetUserPassword, deletePlatformCompany } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function SuperAdmin() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('companies');
  const [companies, setCompanies] = useState([]);
  const [modules, setModules] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [editForm, setEditForm] = useState({ modules: [], max_users: 10, status: 'active' });
  const [usersMap, setUsersMap] = useState({});
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [userForm, setUserForm] = useState({ email: '', full_name: '', password: '', role_names: [] });
  const [passwordReset, setPasswordReset] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');

  const [form, setForm] = useState({
    name: '', code: '', subdomain: '', owner_email: '', owner_name: '', owner_password: '', base_currency: 'USD', activity_type: 'trading', modules: [], max_users: 10
  });
  const [deleteConfirm, setDeleteConfirm] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [compRes, modRes] = await Promise.all([
        getPlatformCompanies(),
        getPlatformModules()
      ]);
      setCompanies(compRes.data || []);
      setModules(modRes.data || []);
      setLoadError('');
    } catch (err) {
      console.error(err);
      setLoadError('Failed to load platform data');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createPlatformCompany(form);
      setShowForm(false);
      setForm({ name: '', code: '', subdomain: '', owner_email: '', owner_name: '', owner_password: '', base_currency: 'USD', activity_type: 'trading', modules: [], max_users: 10 });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating company');
    } finally {
      setLoading(false);
    }
  };

  const handleModuleChange = (modKey) => {
    setForm(prev => {
      const isSelected = prev.modules.includes(modKey);
      return {
        ...prev,
        modules: isSelected ? prev.modules.filter(m => m !== modKey) : [...prev.modules, modKey]
      };
    });
  };

  const handleEditModuleChange = (modKey) => {
    setEditForm(prev => {
      const isSelected = prev.modules.includes(modKey);
      return {
        ...prev,
        modules: isSelected ? prev.modules.filter(m => m !== modKey) : [...prev.modules, modKey]
      };
    });
  };

  const startEdit = (c) => {
    setEditingCompany(c);
    setEditForm({ modules: c.modules || [], max_users: c.max_users || 10, status: c.status || 'active' });
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updatePlatformCompany(editingCompany.id, editForm);
      setEditingCompany(null);
      fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Error updating company'); }
    finally { setLoading(false); }
  };

  const loadUsers = async (company) => {
    setSelectedCompany(company);
    try {
      const res = await getPlatformCompanyUsers(company.id);
      setUsersMap(prev => ({ ...prev, [company.id]: res.data || [] }));
    } catch (err) { alert(err.response?.data?.detail || 'Error loading users'); }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createPlatformCompanyUser(selectedCompany.id, userForm);
      setUserForm({ email: '', full_name: '', password: '', role_names: [] });
      loadUsers(selectedCompany);
    } catch (err) { alert(err.response?.data?.detail || 'Error creating user'); }
    finally { setLoading(false); }
  };

  const handleResetPassword = async (userId) => {
    const newPassword = passwordReset[userId];
    if (!newPassword || newPassword.length < 8) { alert('Enter a new password (min 8 characters)'); return; }
    if (!window.confirm('Reset password for this user?')) return;
    try {
      await resetUserPassword(userId, newPassword);
      setPasswordReset(prev => ({ ...prev, [userId]: '' }));
      alert('Password reset');
    } catch (err) { alert(err.response?.data?.detail || 'Error resetting password'); }
  };

  const handleDeleteCompany = async (company) => {
    const code = deleteConfirm[company.id];
    if (!code || code !== company.code) { alert(`Type the company code "${company.code}" to confirm.`); return; }
    if (!window.confirm(`This will permanently delete ALL data for "${company.name}" (${company.code}). This cannot be undone.`)) return;
    try {
      await deletePlatformCompany(company.id, code);
      setDeleteConfirm(prev => { const n = { ...prev }; delete n[company.id]; return n; });
      fetchData();
      alert('Company deleted');
    } catch (err) { alert(err.response?.data?.detail || 'Error deleting company'); }
  };

  const renderCompanyForm = (c, title, submitLabel, mForm, onModuleChange) => (
    <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ marginBottom: '1.5rem' }}>{title}</h3>
      <form onSubmit={c ? handleSaveEdit : handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label>{t('superadmin.company_name')}</label>
            <input value={mForm.name} onChange={e => c ? setEditForm({...editForm, name: e.target.value}) : setForm({...form, name: e.target.value})} required disabled={!!c} />
          </div>
          <div className="form-group">
            <label>{t('superadmin.company_code')}</label>
            <input value={mForm.code} onChange={e => c ? setEditForm({...editForm, code: e.target.value.toUpperCase()}) : setForm({...form, code: e.target.value.toUpperCase()})} required disabled={!!c} />
          </div>
          <div className="form-group">
            <label>Activity Type</label>
            <select value={mForm.activity_type} onChange={e => c ? setEditForm({...editForm, activity_type: e.target.value}) : setForm({...form, activity_type: e.target.value})} disabled={!!c}>
              <option value="trading">Trading</option>
              <option value="retail">Retail (POS)</option>
              <option value="manufacturing">Manufacturing</option>
              <option value="services">Services</option>
            </select>
          </div>
          <div className="form-group">
            <label>{t('superadmin.max_users')}</label>
            <input type="number" value={mForm.max_users} onChange={e => c ? setEditForm({...editForm, max_users: parseInt(e.target.value)}) : setForm({...form, max_users: parseInt(e.target.value)})} required />
          </div>
          <div className="form-group">
            <label>Status</label>
            {c ? (
              <select value={mForm.status} onChange={e => setEditForm({...editForm, status: e.target.value})}>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
                <option value="trial">Trial</option>
              </select>
            ) : (
              <input value="active" disabled />
            )}
          </div>
        </div>

        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Enabled Modules</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {modules.map(mod => (
            <label key={mod.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={mForm.modules.includes(mod.key)} onChange={() => onModuleChange(mod.key)} />
              <div>
                <div style={{ fontWeight: 600 }}>{mod.label}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{mod.description}</div>
              </div>
            </label>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : submitLabel}
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div>
      {loadError && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--danger)' }}>
          <span>{loadError}</span>
          <button className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={fetchData}>Retry</button>
        </div>
      )}
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'companies' ? 'active' : ''}`} onClick={() => setTab('companies')}>{t('superadmin.companies')}</button>
        <button className={`tab-btn ${tab === 'users' ? 'active' : ''}`} onClick={() => setTab('users')}>Users</button>
      </div>

      {tab === 'companies' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
              {showForm ? t('common.cancel') : `+ ${t('superadmin.create_company')}`}
            </button>
          </div>

          {showForm && renderCompanyForm(
            null,
            'Create New Company (Tenant)',
            'Provision Tenant',
            { ...form, status: 'active' },
            handleModuleChange
          )}

          {editingCompany && renderCompanyForm(
            editingCompany,
            `Edit ${editingCompany.name}`,
            'Save Changes',
            { ...editForm, name: editingCompany.name, code: editingCompany.code, activity_type: editingCompany.activity_type },
            handleEditModuleChange
          )}

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Company Name</th>
                  <th>Code</th>
                  <th>Activity</th>
                  <th>Status</th>
                  <th>Max Users</th>
                  <th>Modules</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {companies.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No companies provisioned</td></tr>
                ) : (
                  companies.map(c => (
                    <tr key={c.id}>
                      <td>{c.id}</td>
                      <td style={{ fontWeight: 600 }}>{c.name}</td>
                      <td>{c.code}</td>
                      <td style={{ textTransform: 'capitalize' }}>{c.activity_type}</td>
                      <td>
                        <span className={`status-badge ${c.status === 'active' ? 'status-completed' : 'status-pending'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td>{c.max_users}</td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{(c.modules || []).join(', ') || '-'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEdit(c)}>Edit</button>
                          <button className="btn" style={{ background: 'rgba(255,255,255,0.08)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => { setTab('users'); loadUsers(c); }}>Users</button>
                        </div>
                        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <input
                            type="text"
                            placeholder={`Type "${c.code}" to delete`}
                            value={deleteConfirm[c.id] || ''}
                            onChange={e => setDeleteConfirm(prev => ({ ...prev, [c.id]: e.target.value }))}
                            style={{ flex: 1, fontSize: '0.75rem', padding: '0.25rem 0.5rem', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: 'var(--danger)' }}
                          />
                          <button
                            className="btn"
                            style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171', padding: '0.25rem 0.75rem', fontSize: '0.75rem', whiteSpace: 'nowrap' }}
                            onClick={() => handleDeleteCompany(c)}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'users' && (
        <div className="dashboard-grid" style={{ gridTemplateColumns: 'minmax(280px, 340px) 1fr', alignItems: 'start' }}>
          <div className="glass-card">
            <h3 style={{ marginBottom: '1rem' }}>Select Company</h3>
            {companies.map(c => (
              <button key={c.id} className={`company-row ${selectedCompany?.id === c.id ? 'selected' : ''}`} onClick={() => loadUsers(c)} style={{ display: 'block', width: '100%', textAlign: 'left', padding: '0.75rem 1rem', marginBottom: '0.5rem', background: selectedCompany?.id === c.id ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', cursor: 'pointer' }}>
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{c.code} • {c.status}</div>
              </button>
            ))}
          </div>

          {selectedCompany ? (
            <div>
              <h3 style={{ marginBottom: '1.5rem' }}>Users — {selectedCompany.name}</h3>
              <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ marginBottom: '1rem' }}>Create User</h4>
                <form onSubmit={handleCreateUser}>
                  <div className="form-grid">
                    <div className="form-group"><label>Full Name</label><input value={userForm.full_name} onChange={e => setUserForm({...userForm, full_name: e.target.value})} required /></div>
                    <div className="form-group"><label>Email</label><input type="email" value={userForm.email} onChange={e => setUserForm({...userForm, email: e.target.value})} required /></div>
                    <div className="form-group"><label>Password</label><input type="password" value={userForm.password} onChange={e => setUserForm({...userForm, password: e.target.value})} required /></div>
                    <div className="form-group"><label>Roles (comma-separated)</label><input value={userForm.role_names.join(', ')} onChange={e => setUserForm({...userForm, role_names: e.target.value.split(',').map(r => r.trim()).filter(Boolean)})} placeholder="admin, sales" /></div>
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={loading}>{loading ? 'Creating...' : 'Create User'}</button>
                </form>
              </div>

              <div className="table-container">
                <table>
                  <thead><tr><th>Name</th><th>Email</th><th>Roles</th><th>Status</th><th>Reset Password</th></tr></thead>
                  <tbody>
                    {(usersMap[selectedCompany.id] || []).length === 0
                      ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No users in this company</td></tr>
                      : (usersMap[selectedCompany.id] || []).map(u => (
                        <tr key={u.id}>
                          <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                          <td>{u.email}</td>
                          <td style={{ fontSize: '0.8rem' }}>{u.roles?.join(', ') || '-'}</td>
                          <td><span className={`status-badge ${u.is_active ? 'status-completed' : 'status-pending'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                              <input type="password" placeholder="New password" value={passwordReset[u.id] || ''} onChange={e => setPasswordReset(prev => ({ ...prev, [u.id]: e.target.value }))} />
                              <button className="btn btn-primary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', whiteSpace: 'nowrap' }} onClick={() => handleResetPassword(u.id)}>Reset</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="glass-card" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '3rem' }}>
              Select a company to manage its users
            </div>
          )}
        </div>
      )}
    </div>
  );
}
