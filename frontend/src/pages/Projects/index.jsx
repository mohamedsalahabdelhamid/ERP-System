import { useState, useEffect } from 'react';
import { getProjects, createProject, addProjectCost, completeProject, getPartners } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Projects() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState([]);
  const [partners, setPartners] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showCostForm, setShowCostForm] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', partner_id: '', start_date: '', end_date: '', contract_value: '' });
  const [costForm, setCostForm] = useState({ cost_type: 'material', description: '', quantity: 1, unit_cost: 0 });
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [proj, par] = await Promise.all([getProjects(), getPartners()]);
      setProjects(proj.data || []);
      setPartners(par.data || []);
    } catch { setProjects([]); }
  };

  const handleCreate = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await createProject({ ...form, partner_id: form.partner_id ? parseInt(form.partner_id) : null, contract_value: parseFloat(form.contract_value || 0) });
      setShowForm(false); setForm({ code: '', name: '', partner_id: '', start_date: '', end_date: '', contract_value: '' }); fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleAddCost = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await addProjectCost(selectedProject.id, { ...costForm, quantity: parseFloat(costForm.quantity), unit_cost: parseFloat(costForm.unit_cost) });
      setShowCostForm(false); setCostForm({ cost_type: 'material', description: '', quantity: 1, unit_cost: 0 }); fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const handleComplete = async (id) => {
    try { await completeProject(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{t('projects.new_project')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{t('projects.new_project')}</h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group"><label>{t('projects.project_code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} placeholder={t('common.auto_code_hint')} /></div>
              <div className="form-group"><label>{t('projects.project_name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
              <div className="form-group">
                <label>{t('projects.client')}</label>
                <select value={form.partner_id} onChange={e => setForm({...form, partner_id: e.target.value})}>
                  <option value="">{t('common.select')}</option>
                  {partners.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>{t('projects.contract_value')}</label><input type="number" step="0.01" value={form.contract_value} onChange={e => setForm({...form, contract_value: e.target.value})} /></div>
              <div className="form-group"><label>{t('projects.start_date')}</label><input type="date" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} /></div>
              <div className="form-group"><label>{t('projects.end_date')}</label><input type="date" value={form.end_date} onChange={e => setForm({...form, end_date: e.target.value})} /></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('projects.create_project')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      {selectedProject && showCostForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{t('projects.add_cost_to', { name: selectedProject.name })}</h3>
          <form onSubmit={handleAddCost}>
            <div className="form-grid">
              <div className="form-group">
                <label>{t('projects.cost_type')}</label>
                <select value={costForm.cost_type} onChange={e => setCostForm({...costForm, cost_type: e.target.value})}>
                  <option value="material">{t('projects.material')}</option>
                  <option value="labor">{t('projects.labor')}</option>
                  <option value="overhead">{t('projects.overhead')}</option>
                </select>
              </div>
              <div className="form-group"><label>{t('projects.description')}</label><input value={costForm.description} onChange={e => setCostForm({...costForm, description: e.target.value})} required /></div>
              <div className="form-group"><label>{t('projects.qty')}</label><input type="number" step="0.01" value={costForm.quantity} onChange={e => setCostForm({...costForm, quantity: e.target.value})} /></div>
              <div className="form-group"><label>{t('projects.unit_cost')}</label><input type="number" step="0.01" value={costForm.unit_cost} onChange={e => setCostForm({...costForm, unit_cost: e.target.value})} /></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('projects.add_cost')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowCostForm(false); setSelectedProject(null); }}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>{t('projects.code')}</th><th>{t('projects.name')}</th><th>{t('projects.contract_value')}</th><th>{t('projects.total_cost')}</th><th>{t('projects.margin')}</th><th>{t('projects.status')}</th><th>{t('projects.actions')}</th></tr></thead>
          <tbody>
            {projects.length === 0
              ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('projects.no_projects')}</td></tr>
              : projects.map(p => {
                const margin = parseFloat(p.contract_value || 0) - parseFloat(p.total_cost || 0);
                return (
                  <tr key={p.id}>
                    <td>{p.code}</td>
                    <td>{p.name}</td>
                    <td>${parseFloat(p.contract_value || 0).toFixed(2)}</td>
                    <td>${parseFloat(p.total_cost || 0).toFixed(2)}</td>
                    <td style={{ color: margin >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>${margin.toFixed(2)}</td>
                    <td><span className={`status-badge ${p.status === 'completed' ? 'status-completed' : 'status-pending'}`}>{p.status}</span></td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn" style={{ background: 'rgba(255,255,255,0.08)', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={() => { setSelectedProject(p); setShowCostForm(true); }}>{t('projects.cost_btn')}</button>
                      {p.status !== 'completed' && <button className="btn btn-primary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={() => handleComplete(p.id)}>{t('projects.complete')}</button>}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
