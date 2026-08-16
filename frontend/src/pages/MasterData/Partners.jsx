import { useState, useEffect } from 'react';
import { getPartners, createPartner, updatePartner, deletePartner } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function Partners() {
  const { t } = useTranslation();
  const [partners, setPartners] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: '', code: '', type: 'customer', phone: '', email: '', address: '' });
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => { fetchPartners(); }, []);

  const fetchPartners = async () => {
    try { const res = await getPartners(); setPartners(res.data || []); } catch { setPartners([]); }
  };

  const resetForm = () => setForm({ name: '', code: '', type: 'customer', phone: '', email: '', address: '' });

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = { name: form.name, code: form.code, type: form.type, phone: form.phone || null, email: form.email || null, address: form.address || null };
      if (editingId) await updatePartner(editingId, payload);
      else await createPartner(payload);
      setShowForm(false);
      setEditingId(null);
      resetForm();
      fetchPartners();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  const startEdit = (p) => {
    setEditingId(p.id);
    setForm({ name: p.name, code: p.code, type: p.type, phone: p.phone || '', email: p.email || '', address: p.address || '' });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('partners.delete_partner'))) return;
    try { await deletePartner(id); fetchPartners(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const filtered = filterType === 'all' ? partners : partners.filter(p => p.type === filterType);

  return (
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center' }}>
        <div className="tab-bar">
          <button className={`tab-btn ${filterType === 'all' ? 'active' : ''}`} onClick={() => setFilterType('all')}>{t('partners.all')}</button>
          <button className={`tab-btn ${filterType === 'customer' ? 'active' : ''}`} onClick={() => setFilterType('customer')}>{t('partners.customers')}</button>
          <button className={`tab-btn ${filterType === 'supplier' ? 'active' : ''}`} onClick={() => setFilterType('supplier')}>{t('partners.suppliers')}</button>
        </div>
        <button className="btn btn-primary" style={{ marginLeft: 'auto' }} onClick={() => { setEditingId(null); resetForm(); setShowForm(!showForm); }}>{t('partners.add_partner')}</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? t('partners.edit_partner') : t('partners.new_partner')}</h3>
          <form onSubmit={handleSave}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('partners.name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('partners.code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                  <div className="form-group">
                    <label>{t('partners.type')}</label>
                    <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                      <option value="customer">{t('partners.customer')}</option>
                      <option value="supplier">{t('partners.supplier')}</option>
                      <option value="both">{t('partners.both')}</option>
                    </select>
                  </div>
                  <div className="form-group"><label>{t('partners.phone')}</label><input value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} /></div>
                  <div className="form-group"><label>{t('partners.email')}</label><input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
                  <div className="form-group" style={{ gridColumn: '1/-1' }}><label>{t('partners.address')}</label><textarea value={form.address} onChange={e => setForm({...form, address: e.target.value})} rows={2} /></div>
                </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('partners.save_partner')}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>{t('common.cancel')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>#</th><th>{t('partners.name')}</th><th>{t('partners.type')}</th><th>{t('partners.phone')}</th><th>{t('partners.email')}</th><th></th></tr></thead>
          <tbody>
            {filtered.length === 0
              ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('partners.no_partners')}</td></tr>
              : filtered.map((p, i) => (
                <tr key={p.id}>
                  <td>{i + 1}</td>
                  <td>{p.name}</td>
                  <td><span className={`status-badge ${p.type === 'customer' ? 'status-completed' : 'status-pending'}`}>{p.type}</span></td>
                  <td>{p.phone || '-'}</td>
                  <td>{p.email || '-'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEdit(p)}>{t('partners.edit')}</button>
                      <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDelete(p.id)}>{t('partners.delete')}</button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
