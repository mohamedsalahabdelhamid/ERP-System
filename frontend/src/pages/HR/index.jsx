import { useState, useEffect } from 'react';
import { getEmployees, createEmployee, getDepartments, createDepartment, runPayroll, createAttendance } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function HR() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', employee_number: '', position: '', department_id: '', basic_salary: '', hire_date: '' });
  const [payrollPeriod, setPayrollPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [loading, setLoading] = useState(false);
  const [payrollResult, setPayrollResult] = useState(null);
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [deptForm, setDeptForm] = useState({ name: '' });
  const [attForm, setAttForm] = useState({ employee_id: '', date: new Date().toISOString().split('T')[0], status: 'present', note: '' });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [emp, dep] = await Promise.all([getEmployees(), getDepartments()]);
      setEmployees(emp.data || []);
      setDepartments(dep.data || []);
    } catch { setEmployees([]); setDepartments([]); }
  };

  const handleCreateEmployee = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await createEmployee({ ...form, basic_salary: parseFloat(form.basic_salary), department_id: form.department_id ? parseInt(form.department_id) : null });
      setShowForm(false);
      setForm({ name: '', employee_number: '', position: '', department_id: '', basic_salary: '', hire_date: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handlePayroll = async () => {
    setLoading(true);
    try {
      const res = await runPayroll({ period: payrollPeriod });
      setPayrollResult(res.data);
    } catch (err) { alert(err.response?.data?.detail || 'Error running payroll'); }
    finally { setLoading(false); }
  };

  const handleCreateDepartment = async (e) => {
    e.preventDefault();
    try {
      await createDepartment(deptForm);
      setShowDeptForm(false);
      setDeptForm({ name: '' });
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating department'); }
  };

  const handleCreateAttendance = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createAttendance({ ...attForm, employee_id: parseInt(attForm.employee_id), note: attForm.note || null });
      setAttForm({ employee_id: '', date: new Date().toISOString().split('T')[0], status: 'present', note: '' });
      alert(t('hr.attendance_recorded'));
    } catch (err) { alert(err.response?.data?.detail || t('hr.error_attendance')); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        <button className={`tab-btn ${tab === 'employees' ? 'active' : ''}`} onClick={() => setTab('employees')}>{t('hr.tab_employees')}</button>
        <button className={`tab-btn ${tab === 'departments' ? 'active' : ''}`} onClick={() => setTab('departments')}>{t('hr.tab_departments')}</button>
        <button className={`tab-btn ${tab === 'attendance' ? 'active' : ''}`} onClick={() => setTab('attendance')}>{t('hr.tab_attendance')}</button>
        <button className={`tab-btn ${tab === 'payroll' ? 'active' : ''}`} onClick={() => setTab('payroll')}>{t('hr.tab_payroll')}</button>
      </div>

      {tab === 'employees' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('hr.add_employee')}</button>
          </div>
          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('hr.new_employee')}</h3>
              <form onSubmit={handleCreateEmployee}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('hr.full_name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('hr.employee_no')}</label><input value={form.employee_number} onChange={e => setForm({...form, employee_number: e.target.value})} placeholder={t('common.auto_code_hint')} /></div>
                  <div className="form-group"><label>{t('hr.position')}</label><input value={form.position} onChange={e => setForm({...form, position: e.target.value})} /></div>
                  <div className="form-group">
                    <label>{t('hr.department')}</label>
                    <select value={form.department_id} onChange={e => setForm({...form, department_id: e.target.value})}>
                      <option value="">{t('common.select')}</option>
                      {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>{t('hr.basic_salary')}</label><input type="number" step="0.01" value={form.basic_salary} onChange={e => setForm({...form, basic_salary: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('hr.hire_date')}</label><input type="date" value={form.hire_date} onChange={e => setForm({...form, hire_date: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('hr.save_employee')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>{t('hr.no')}</th><th>{t('hr.name')}</th><th>{t('hr.position')}</th><th>{t('hr.department')}</th><th>{t('hr.basic_salary')}</th><th>{t('hr.status')}</th></tr></thead>
              <tbody>
                {employees.length === 0
                  ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('hr.no_employees')}</td></tr>
                  : employees.map(emp => (
                    <tr key={emp.id}>
                      <td>{emp.employee_number}</td>
                      <td>{emp.name}</td>
                      <td>{emp.position || '-'}</td>
                      <td>{departments.find(d => d.id === emp.department_id)?.name || emp.department_id || '-'}</td>
                      <td>${parseFloat(emp.basic_salary || 0).toFixed(2)}</td>
                      <td><span className={`status-badge ${emp.is_active ? 'status-completed' : 'status-pending'}`}>{emp.is_active ? t('hr.active') : t('hr.inactive')}</span></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'departments' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowDeptForm(!showDeptForm)}>{t('hr.add_department')}</button>
          </div>
          {showDeptForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('hr.new_department')}</h3>
              <form onSubmit={handleCreateDepartment}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('hr.department_name')}</label><input value={deptForm.name} onChange={e => setDeptForm({...deptForm, name: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">{t('hr.save_department')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowDeptForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('hr.department_name')}</th></tr></thead>
              <tbody>
                {departments.length === 0
                  ? <tr><td colSpan={2} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('hr.no_departments')}</td></tr>
                  : departments.map((d, i) => <tr key={d.id}><td>{i + 1}</td><td>{d.name}</td></tr>)}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'attendance' && (
        <div className="glass-card" style={{ maxWidth: '560px' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{t('hr.record_attendance')}</h3>
          <form onSubmit={handleCreateAttendance}>
            <div className="form-grid">
              <div className="form-group">
                <label>{t('hr.employee')}</label>
                <select value={attForm.employee_id} onChange={e => setAttForm({...attForm, employee_id: e.target.value})} required>
                  <option value="">{t('common.select')}</option>
                  {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>{t('hr.date')}</label><input type="date" value={attForm.date} onChange={e => setAttForm({...attForm, date: e.target.value})} required /></div>
              <div className="form-group">
                <label>{t('hr.attendance_status')}</label>
                <select value={attForm.status} onChange={e => setAttForm({...attForm, status: e.target.value})}>
                  <option value="present">{t('hr.present')}</option>
                  <option value="absent">{t('hr.absent')}</option>
                  <option value="leave">{t('hr.leave')}</option>
                  <option value="late">{t('hr.late')}</option>
                </select>
              </div>
              <div className="form-group"><label>{t('hr.note')}</label><input value={attForm.note} onChange={e => setAttForm({...attForm, note: e.target.value})} /></div>
            </div>
            <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={loading}>{loading ? t('common.saving') : t('hr.record_attendance')}</button>
          </form>
        </div>
      )}

      {tab === 'payroll' && (
        <div>
          <div className="glass-card" style={{ marginBottom: '1.5rem', maxWidth: '400px' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>{t('hr.run_payroll')}</h3>
            <div className="form-group">
              <label>{t('hr.payroll_period')}</label>
              <input type="month" value={payrollPeriod} onChange={e => setPayrollPeriod(e.target.value)} />
            </div>
            <button className="btn btn-primary" style={{ marginTop: '1rem', width: '100%' }} onClick={handlePayroll} disabled={loading}>
              {loading ? t('common.processing') : t('hr.run_payroll')}
            </button>
          </div>

          {payrollResult && (
            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              <div className="glass-card"><div className="kpi-title">{t('hr.payroll_period')}</div><div className="kpi-value" style={{ fontSize: '1.5rem' }}>{payrollResult.period}</div></div>
              <div className="glass-card"><div className="kpi-title">{t('hr.total_gross')}</div><div className="kpi-value" style={{ fontSize: '1.5rem' }}>${parseFloat(payrollResult.total_gross || 0).toFixed(2)}</div></div>
              <div className="glass-card"><div className="kpi-title">{t('hr.total_net_pay')}</div><div className="kpi-value" style={{ fontSize: '1.5rem', color: 'var(--success)' }}>${parseFloat(payrollResult.total_net || 0).toFixed(2)}</div></div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
