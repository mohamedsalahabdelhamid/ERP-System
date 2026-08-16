import { useState, useEffect } from 'react';
import { getLeaveRequests, createLeaveRequest, updateLeaveStatus, getEmployees } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function LeaveRequests() {
  const { t } = useTranslation();
  const [requests, setRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    employee_id: '', leave_type: 'annual', start_date: '', end_date: '', days: 1, reason: '',
  });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [r, e] = await Promise.all([getLeaveRequests(), getEmployees()]);
      setRequests(r.data || []);
      setEmployees(e.data || []);
    } catch { setRequests([]); setEmployees([]); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.employee_id) { alert(t('leaverequests.select_employee_err')); return; }
    if (!form.start_date || !form.end_date) { alert(t('leaverequests.select_dates_err')); return; }
    if (form.end_date < form.start_date) { alert(t('leaverequests.date_order_err')); return; }
    const days = Math.max(1, Math.round((new Date(form.end_date) - new Date(form.start_date)) / 86400000) + 1);
    setLoading(true);
    try {
      await createLeaveRequest({
        ...form,
        employee_id: Number(form.employee_id),
        days,
      });
      setShowForm(false);
      setForm({ employee_id: '', leave_type: 'annual', start_date: '', end_date: '', days: 1, reason: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleStatus = async (id, status) => {
    try { await updateLeaveStatus(id, status); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const empName = (id) => {
    const em = employees.find(e => e.id === id);
    return em ? `${em.employee_number} — ${em.name}` : `#${id}`;
  };

  const badge = (status) => (
    <span className={`status-badge ${
      status === 'approved' ? 'status-completed'
      : status === 'rejected' ? 'status-failed'
      : status === 'cancelled' ? 'status-cancelled'
      : 'status-pending'
    }`}>{status}</span>
  );

  const typeLabel = { annual: `🌴 ${t('leaverequests.annual')}`, sick: `🤒 ${t('leaverequests.sick')}`, unpaid: `🚫 ${t('leaverequests.unpaid')}` };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('leaverequests.new_request')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>{t('leaverequests.employee')}</label>
                <select value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })} required>
                  <option value="">{t('leaverequests.select_employee')}</option>
                  {employees.map(em => <option key={em.id} value={em.id}>{em.employee_number} — {em.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>{t('leaverequests.leave_type')}</label>
                <select value={form.leave_type} onChange={e => setForm({ ...form, leave_type: e.target.value })}>
                  <option value="annual">{t('leaverequests.annual')}</option>
                  <option value="sick">{t('leaverequests.sick')}</option>
                  <option value="unpaid">{t('leaverequests.unpaid')}</option>
                </select>
              </div>
              <div className="form-group"><label>{t('leaverequests.start_date')}</label><input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} required /></div>
              <div className="form-group"><label>{t('leaverequests.end_date')}</label><input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} required /></div>
              <div className="form-group"><label>{t('leaverequests.days')}</label><input type="number" step="0.5" value={form.start_date && form.end_date && form.end_date >= form.start_date ? Math.round((new Date(form.end_date) - new Date(form.start_date)) / 86400000) + 1 : form.days} readOnly /></div>
              <div className="form-group"><label>{t('leaverequests.reason')}</label><input value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} /></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('leaverequests.submit')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>{t('leaverequests.employee')}</th><th>{t('leaverequests.leave_type')}</th><th>{t('leaverequests.period')}</th><th>{t('leaverequests.days')}</th><th>{t('leaverequests.reason')}</th><th>{t('leaverequests.status')}</th><th>{t('leaverequests.actions')}</th></tr></thead>
          <tbody>
            {requests.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('leaverequests.no_requests')}</td></tr>
              : requests.map(r => (
                <tr key={r.id}>
                  <td>{empName(r.employee_id)}</td>
                  <td>{typeLabel[r.leave_type] || r.leave_type}</td>
                  <td style={{ fontSize: '0.85rem' }}>{r.start_date} → {r.end_date}</td>
                  <td>{parseFloat(r.days || 0)}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{r.reason || '—'}</td>
                  <td>{badge(r.status)}</td>
                  <td>
                    {r.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-primary" style={{ padding: '0.3rem 0.8rem' }} onClick={() => handleStatus(r.id, 'approved')}>{t('leaverequests.approve')}</button>
                        <button className="btn" style={{ background: 'rgba(255,0,0,0.15)', padding: '0.3rem 0.8rem' }} onClick={() => handleStatus(r.id, 'rejected')}>{t('leaverequests.reject')}</button>
                        <button className="btn" style={{ background: 'rgba(255,255,255,0.1)', padding: '0.3rem 0.8rem' }} onClick={() => handleStatus(r.id, 'cancelled')}>{t('leaverequests.cancel')}</button>
                      </div>
                    )}
                    {r.status !== 'pending' && <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
