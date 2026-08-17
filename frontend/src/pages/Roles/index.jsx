import { useState, useEffect } from 'react';
import {
  getPermissions, getRoles, createRole, updateRolePermissions, deleteRole,
  getCompanyUsers, createCompanyUser, updateCompanyUserRoles, updateCompanyUserStatus,
} from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Roles() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('roles');
  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newRoleName, setNewRoleName] = useState('');
  const [expandedRole, setExpandedRole] = useState(null);
  const [rolePerms, setRolePerms] = useState({});
  const [editingUserRoles, setEditingUserRoles] = useState(null);
  const [toast, setToast] = useState(null);
  const [userForm, setUserForm] = useState({ email: '', full_name: '', password: '', role_names: ['Employee'] });

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [p, r, u] = await Promise.all([getPermissions(), getRoles(), getCompanyUsers()]);
      setPermissions(p.data || []);
      setRoles(r.data || []);
      setUsers(u.data || []);
    } catch (err) {
      showToast('Failed to load data', 'error');
    } finally { setLoading(false); }
  };

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    if (!newRoleName.trim()) return;
    try {
      await createRole({ name: newRoleName.trim(), permissions: [] });
      setNewRoleName('');
      const r = await getRoles();
      setRoles(r.data || []);
      showToast(`Role "${newRoleName.trim()}" created`);
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const handleTogglePerm = (roleId, code) => {
    setRolePerms(prev => {
      const current = prev[roleId] || roles.find(r => r.id === roleId)?.permissions || [];
      const next = current.includes(code) ? current.filter(c => c !== code) : [...current, code];
      return { ...prev, [roleId]: next };
    });
  };

  const handleSavePermissions = async (roleId) => {
    const perms = rolePerms[roleId];
    if (perms === undefined) return;
    try {
      await updateRolePermissions(roleId, perms);
      setRoles(prev => prev.map(r => r.id === roleId ? { ...r, permissions: perms } : r));
      setExpandedRole(null);
      showToast('Permissions saved');
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const handleDeleteRole = async (role) => {
    if (!window.confirm(`Delete role "${role.name}"?`)) return;
    try {
      await deleteRole(role.id);
      setRoles(prev => prev.filter(r => r.id !== role.id));
      showToast(`Role "${role.name}" deleted`);
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await createCompanyUser(userForm);
      setUserForm({ email: '', full_name: '', password: '', role_names: ['Employee'] });
      const u = await getCompanyUsers();
      setUsers(u.data || []);
      showToast('User created');
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const handleSaveUserRoles = async (userId) => {
    const roleNames = editingUserRoles[userId];
    if (!roleNames) return;
    try {
      const res = await updateCompanyUserRoles(userId, roleNames);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, roles: res.data.roles } : u));
      setEditingUserRoles(null);
      showToast('Roles updated');
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const handleToggleUserActive = async (user) => {
    try {
      await updateCompanyUserStatus(user.id, !user.is_active);
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, is_active: !u.is_active } : u));
    } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
  };

  const permsByModule = {};
  permissions.forEach(p => {
    const mod = p.code.split('.')[0];
    if (!permsByModule[mod]) permsByModule[mod] = [];
    permsByModule[mod].push(p);
  });

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>{t('common.loading')}</div>;

  return (
    <div>
      {toast && (
        <div style={{
          position: 'fixed', top: '1.5rem', right: '1.5rem', zIndex: 9999,
          padding: '0.875rem 1.5rem', borderRadius: '10px', fontWeight: 600, fontSize: '0.9rem',
          background: toast.type === 'success' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
          border: `1px solid ${toast.type === 'success' ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
          color: toast.type === 'success' ? 'var(--success)' : 'var(--danger)',
          backdropFilter: 'blur(16px)', animation: 'fadeIn 0.3s ease',
        }}>{toast.msg}</div>
      )}

      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'roles' ? 'active' : ''}`} onClick={() => setTab('roles')}>{t('roles.tab_roles')}</button>
        <button className={`tab-btn ${tab === 'users' ? 'active' : ''}`} onClick={() => setTab('users')}>{t('roles.tab_users')}</button>
      </div>

      {tab === 'roles' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px' }}>
          <div className="glass-card">
            <h3 style={{ marginBottom: '1rem' }}>{t('roles.create_role')}</h3>
            <form onSubmit={handleCreateRole} style={{ display: 'flex', gap: '1rem', alignItems: 'end' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>{t('roles.role_name')}</label>
                <input value={newRoleName} onChange={e => setNewRoleName(e.target.value)} placeholder={t('roles.role_name_placeholder')} required />
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginBottom: '4px' }}>{t('common.add')}</button>
            </form>
          </div>

          {roles.map(role => {
            const isExpanded = expandedRole === role.id;
            const currentPerms = rolePerms[role.id] ?? role.permissions;
            return (
              <div key={role.id} className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{role.name}</h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      {role.permissions.length} {t('roles.permissions_assigned')}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                      onClick={() => { setExpandedRole(isExpanded ? null : role.id); setRolePerms(prev => ({ ...prev, [role.id]: role.permissions })); }}>
                      {isExpanded ? t('common.cancel') : t('roles.edit_permissions')}
                    </button>
                    {role.name.toLowerCase() !== 'admin' && (
                      <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171', padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                        onClick={() => handleDeleteRole(role)}>
                        {t('common.delete')}
                      </button>
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
                    {Object.entries(permsByModule).map(([mod, perms]) => (
                      <div key={mod} style={{ marginBottom: '1rem' }}>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary-color)', marginBottom: '0.5rem', textTransform: 'capitalize' }}>{mod}</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                          {perms.map(p => (
                            <label key={p.code} style={{
                              display: 'flex', alignItems: 'center', gap: '0.4rem',
                              padding: '0.3rem 0.75rem', borderRadius: '6px', fontSize: '0.78rem',
                              background: currentPerms.includes(p.code) ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                              border: `1px solid ${currentPerms.includes(p.code) ? 'rgba(16,185,129,0.35)' : 'rgba(255,255,255,0.08)'}`,
                              cursor: 'pointer', transition: 'all 0.15s',
                            }}>
                              <input type="checkbox" checked={currentPerms.includes(p.code)}
                                onChange={() => handleTogglePerm(role.id, p.code)}
                                style={{ accentColor: 'var(--success)' }} />
                              <span>{p.code}</span>
                              {p.description && <span style={{ color: 'var(--text-secondary)', fontSize: '0.72rem' }}>({p.description})</span>}
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                    <button className="btn btn-primary" style={{ marginTop: '0.5rem' }} onClick={() => handleSavePermissions(role.id)}>
                      {t('common.save')}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {tab === 'users' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px' }}>
          <div className="glass-card">
            <h3 style={{ marginBottom: '1rem' }}>{t('roles.create_user')}</h3>
            <form onSubmit={handleCreateUser}>
              <div className="form-grid">
                <div className="form-group"><label>{t('roles.full_name')}</label><input value={userForm.full_name} onChange={e => setUserForm({...userForm, full_name: e.target.value})} required /></div>
                <div className="form-group"><label>{t('roles.email')}</label><input type="email" value={userForm.email} onChange={e => setUserForm({...userForm, email: e.target.value})} required /></div>
                <div className="form-group"><label>{t('roles.password')}</label><input type="password" value={userForm.password} onChange={e => setUserForm({...userForm, password: e.target.value})} required minLength={8} /></div>
                <div className="form-group">
                  <label>{t('roles.assign_roles')}</label>
                  <input value={userForm.role_names.join(', ')} onChange={e => setUserForm({...userForm, role_names: e.target.value.split(',').map(r => r.trim()).filter(Boolean)})} placeholder="Employee, Sales" />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{t('roles.roles_hint')}</span>
                </div>
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }}>{t('common.add')}</button>
            </form>
          </div>

          <div className="glass-card">
            <h3 style={{ marginBottom: '1rem' }}>{t('roles.company_users')}</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>{t('roles.full_name')}</th>
                    <th>{t('roles.email')}</th>
                    <th>{t('roles.col_roles')}</th>
                    <th>{t('common.status')}</th>
                    <th>{t('roles.assign_roles')}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('roles.no_users')}</td></tr>
                  ) : users.map(u => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                      <td>{u.email}</td>
                      <td style={{ fontSize: '0.8rem' }}>{u.roles?.join(', ') || '-'}</td>
                      <td>
                        <span className={`status-badge ${u.is_active ? 'status-completed' : 'status-pending'}`}
                          style={{ cursor: 'pointer' }} onClick={() => handleToggleUserActive(u)}>
                          {u.is_active ? t('common.active') : t('common.inactive')}
                        </span>
                      </td>
                      <td>
                        {editingUserRoles?.[u.id] !== undefined ? (
                          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <input
                              style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem', width: '180px' }}
                              value={editingUserRoles[u.id].join(', ')}
                              onChange={e => setEditingUserRoles(prev => ({ ...prev, [u.id]: e.target.value.split(',').map(r => r.trim()).filter(Boolean) }))}
                            />
                            <button className="btn btn-primary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={() => handleSaveUserRoles(u.id)}>{t('common.save')}</button>
                            <button className="btn" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.08)' }} onClick={() => setEditingUserRoles(prev => { const n = { ...prev }; delete n[u.id]; return n; })}>{t('common.cancel')}</button>
                          </div>
                        ) : (
                          <button className="btn" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => setEditingUserRoles(prev => ({ ...prev, [u.id]: [...(u.roles || [])] }))}>
                            {t('roles.edit_roles')}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
