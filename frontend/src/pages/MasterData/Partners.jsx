import { useState, useEffect } from 'react';
import { getPartners, createPartner, updatePartner, deletePartner } from '../../api/client';

export default function Partners() {
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
    if (!window.confirm('Delete this partner?')) return;
    try { await deletePartner(id); fetchPartners(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const filtered = filterType === 'all' ? partners : partners.filter(p => p.type === filterType);

  return (
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center' }}>
        <div className="tab-bar">
          <button className={`tab-btn ${filterType === 'all' ? 'active' : ''}`} onClick={() => setFilterType('all')}>All</button>
          <button className={`tab-btn ${filterType === 'customer' ? 'active' : ''}`} onClick={() => setFilterType('customer')}>Customers</button>
          <button className={`tab-btn ${filterType === 'supplier' ? 'active' : ''}`} onClick={() => setFilterType('supplier')}>Suppliers</button>
        </div>
        <button className="btn btn-primary" style={{ marginLeft: 'auto' }} onClick={() => { setEditingId(null); resetForm(); setShowForm(!showForm); }}>+ Add Partner</button>
      </div>

      {showForm && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? 'Edit Partner' : 'New Partner'}</h3>
          <form onSubmit={handleSave}>
                <div className="form-grid">
                  <div className="form-group"><label>Name</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>Code</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                  <div className="form-group">
                    <label>Type</label>
                    <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                      <option value="customer">Customer</option>
                      <option value="supplier">Supplier</option>
                      <option value="both">Both</option>
                    </select>
                  </div>
                  <div className="form-group"><label>Phone</label><input value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} /></div>
                  <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
                  <div className="form-group" style={{ gridColumn: '1/-1' }}><label>Address</label><textarea value={form.address} onChange={e => setForm({...form, address: e.target.value})} rows={2} /></div>
                </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Save Partner'}</button>
              <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Type</th><th>Phone</th><th>Email</th><th></th></tr></thead>
          <tbody>
            {filtered.length === 0
              ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No partners found</td></tr>
              : filtered.map((p, i) => (
                <tr key={p.id}>
                  <td>{i + 1}</td>
                  <td>{p.name}</td>
                  <td><span className={`status-badge ${p.type === 'customer' ? 'status-completed' : 'status-pending'}`}>{p.type}</span></td>
                  <td>{p.phone || '-'}</td>
                  <td>{p.email || '-'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEdit(p)}>Edit</button>
                      <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDelete(p.id)}>Delete</button>
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
