import { useState, useEffect } from 'react';
import { getItems, createItem, updateItem, deleteItem, getCategories, createCategory, deleteCategory, getUnits, createUnit, deleteUnit, getUnitConversions, createUnitConversion, deleteUnitConversion } from '../../api/client';

export default function MasterData() {
  const [tab, setTab] = useState('items');
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [conversions, setConversions] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showCatForm, setShowCatForm] = useState(false);
  const [showUnitForm, setShowUnitForm] = useState(false);
  const [showConvForm, setShowConvForm] = useState(false);
  const [form, setForm] = useState({ name: '', code: '', item_category_id: '', base_unit_id: '', type: 'stock', default_sale_price: '', default_purchase_price: '', min_stock_level: '' });
  const [catForm, setCatForm] = useState({ name: '', code: '' });
  const [unitForm, setUnitForm] = useState({ name: '', code: '', symbol: '' });
  const [convForm, setConvForm] = useState({ from_unit_id: '', to_unit_id: '', factor: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [itemsRes, catsRes, unitsRes, convRes] = await Promise.all([getItems(), getCategories(), getUnits(), getUnitConversions()]);
      setItems(itemsRes.data || []);
      setCategories(catsRes.data || []);
      setUnits(unitsRes.data || []);
      setConversions(convRes.data || []);
    } catch { setItems([]); setCategories([]); setUnits([]); setConversions([]); }
  };

  const catName = (id) => (categories.find(c => c.id === id) || {}).name || '-';
  const unitName = (id) => (units.find(u => u.id === id) || {}).name || '-';

  const resetItemForm = () => setForm({ name: '', code: '', item_category_id: '', base_unit_id: '', type: 'stock', default_sale_price: '', default_purchase_price: '', min_stock_level: '' });

  const handleSaveItem = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        code: form.code,
        type: form.type,
        item_category_id: form.item_category_id ? parseInt(form.item_category_id) : null,
        base_unit_id: form.base_unit_id ? parseInt(form.base_unit_id) : null,
        default_sale_price: parseFloat(form.default_sale_price || 0),
        default_purchase_price: parseFloat(form.default_purchase_price || 0),
        min_stock_level: parseFloat(form.min_stock_level || 0),
      };
      if (editingId) await updateItem(editingId, payload);
      else await createItem(payload);
      setShowForm(false);
      setEditingId(null);
      resetItemForm();
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error saving item');
    } finally { setLoading(false); }
  };

  const startEditItem = (item) => {
    setEditingId(item.id);
    setForm({
      name: item.name, code: item.code,
      item_category_id: item.item_category_id || '',
      base_unit_id: item.base_unit_id || '',
      type: item.type,
      default_sale_price: item.default_sale_price, default_purchase_price: item.default_purchase_price,
      min_stock_level: item.min_stock_level,
    });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDeleteItem = async (id) => {
    if (!window.confirm('Delete this item?')) return;
    try { await deleteItem(id); fetchData(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleSaveCategory = async (e) => {
    e.preventDefault();
    try {
      await createCategory({ name: catForm.name, code: catForm.code });
      setShowCatForm(false);
      setCatForm({ name: '', code: '' });
      fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating category'); }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Delete this category?')) return;
    try { await deleteCategory(id); fetchData(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleSaveUnit = async (e) => {
    e.preventDefault();
    try {
      await createUnit({ name: unitForm.name, code: unitForm.code, symbol: unitForm.symbol || null });
      setShowUnitForm(false);
      setUnitForm({ name: '', code: '', symbol: '' });
      fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating unit'); }
  };

  const handleDeleteUnit = async (id) => {
    if (!window.confirm('Delete this unit?')) return;
    try { await deleteUnit(id); fetchData(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleSaveConversion = async (e) => {
    e.preventDefault();
    try {
      await createUnitConversion({ from_unit_id: parseInt(convForm.from_unit_id), to_unit_id: parseInt(convForm.to_unit_id), factor: parseFloat(convForm.factor) });
      setShowConvForm(false);
      setConvForm({ from_unit_id: '', to_unit_id: '', factor: '' });
      fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Error creating conversion'); }
  };

  const handleDeleteConversion = async (id) => {
    if (!window.confirm('Delete this conversion?')) return;
    try { await deleteUnitConversion(id); fetchData(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  return (
    <div>
      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'items' ? 'active' : ''}`} onClick={() => setTab('items')}>Items</button>
        <button className={`tab-btn ${tab === 'categories' ? 'active' : ''}`} onClick={() => setTab('categories')}>Categories</button>
        <button className={`tab-btn ${tab === 'units' ? 'active' : ''}`} onClick={() => setTab('units')}>Units</button>
        <button className={`tab-btn ${tab === 'conversions' ? 'active' : ''}`} onClick={() => setTab('conversions')}>Unit Conversions</button>
      </div>

      {tab === 'items' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => { setEditingId(null); resetItemForm(); setShowForm(!showForm); }}>+ Add Item</button>
          </div>

          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? 'Edit Item' : 'New Item'}</h3>
              <form onSubmit={handleSaveItem}>
                <div className="form-grid">
                  <div className="form-group"><label>Item Name</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>Item Code</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></div>
                  <div className="form-group">
                    <label>Type</label>
                    <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                      <option value="stock">Stock</option>
                      <option value="service">Service</option>
                      <option value="manufactured">Manufactured</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Category</label>
                    <select value={form.item_category_id} onChange={e => setForm({...form, item_category_id: e.target.value})}>
                      <option value="">-- Select --</option>
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Base Unit</label>
                    <select value={form.base_unit_id} onChange={e => setForm({...form, base_unit_id: e.target.value})}>
                      <option value="">-- Select --</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>Sale Price</label><input type="number" step="0.01" value={form.default_sale_price} onChange={e => setForm({...form, default_sale_price: e.target.value})} /></div>
                  <div className="form-group"><label>Purchase Price</label><input type="number" step="0.01" value={form.default_purchase_price} onChange={e => setForm({...form, default_purchase_price: e.target.value})} /></div>
                  <div className="form-group"><label>Min Stock Level</label><input type="number" step="0.01" value={form.min_stock_level} onChange={e => setForm({...form, min_stock_level: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : 'Save Item'}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>Code</th><th>Name</th><th>Category</th><th>Type</th><th>Sale Price</th><th>Cost Price</th><th>Min Stock</th><th></th></tr></thead>
              <tbody>
                {items.length === 0 ? <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No items found</td></tr>
                : items.map((item, i) => (
                  <tr key={item.id}>
                    <td>{i + 1}</td>
                    <td>{item.code}</td>
                    <td>{item.name}</td>
                    <td>{catName(item.item_category_id)}</td>
                    <td><span className="status-badge status-pending" style={{ fontSize: '0.7rem' }}>{item.type}</span></td>
                    <td>${parseFloat(item.default_sale_price || 0).toFixed(2)}</td>
                    <td>${parseFloat(item.default_purchase_price || 0).toFixed(2)}</td>
                    <td>{parseFloat(item.min_stock_level || 0).toFixed(2)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEditItem(item)}>Edit</button>
                        <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteItem(item.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'categories' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowCatForm(!showCatForm)}>+ Add Category</button>
          </div>
          {showCatForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>New Category</h3>
              <form onSubmit={handleSaveCategory}>
                <div className="form-grid">
                  <div className="form-group"><label>Category Name</label><input value={catForm.name} onChange={e => setCatForm({...catForm, name: e.target.value})} required /></div>
                  <div className="form-group"><label>Code</label><input value={catForm.code} onChange={e => setCatForm({...catForm, code: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">Save Category</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowCatForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>Category Name</th><th>Code</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {categories.length === 0 ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No categories yet</td></tr>
                : categories.map((c, i) => (
                  <tr key={c.id}>
                    <td>{i + 1}</td>
                    <td>{c.name}</td>
                    <td>{c.code}</td>
                    <td><span className={`status-badge ${c.is_active ? 'status-completed' : 'status-pending'}`}>{c.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteCategory(c.id)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'units' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowUnitForm(!showUnitForm)}>+ Add Unit</button>
          </div>
          {showUnitForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>New Unit</h3>
              <form onSubmit={handleSaveUnit}>
                <div className="form-grid">
                  <div className="form-group"><label>Unit Name</label><input value={unitForm.name} onChange={e => setUnitForm({...unitForm, name: e.target.value})} required /></div>
                  <div className="form-group"><label>Code</label><input value={unitForm.code} onChange={e => setUnitForm({...unitForm, code: e.target.value})} required /></div>
                  <div className="form-group"><label>Symbol</label><input value={unitForm.symbol} onChange={e => setUnitForm({...unitForm, symbol: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">Save Unit</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowUnitForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>Unit Name</th><th>Code</th><th>Symbol</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {units.length === 0 ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No units yet</td></tr>
                : units.map((u, i) => (
                  <tr key={u.id}>
                    <td>{i + 1}</td>
                    <td>{u.name}</td>
                    <td>{u.code}</td>
                    <td>{u.symbol || '-'}</td>
                    <td><span className={`status-badge ${u.is_active ? 'status-completed' : 'status-pending'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteUnit(u.id)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'conversions' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowConvForm(!showConvForm)}>+ Add Conversion</button>
          </div>
          {showConvForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>New Unit Conversion</h3>
              <form onSubmit={handleSaveConversion}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>From Unit</label>
                    <select value={convForm.from_unit_id} onChange={e => setConvForm({...convForm, from_unit_id: e.target.value})} required>
                      <option value="">-- Select --</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>To Unit</label>
                    <select value={convForm.to_unit_id} onChange={e => setConvForm({...convForm, to_unit_id: e.target.value})} required>
                      <option value="">-- Select --</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>Factor (1 From = X To)</label><input type="number" min="0" step="0.0001" value={convForm.factor} onChange={e => setConvForm({...convForm, factor: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">Save Conversion</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowConvForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>From Unit</th><th>To Unit</th><th>Factor</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {conversions.length === 0 ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No unit conversions yet</td></tr>
                : conversions.map((conv, i) => (
                  <tr key={conv.id}>
                    <td>{i + 1}</td>
                    <td>{unitName(conv.from_unit_id)}</td>
                    <td>{unitName(conv.to_unit_id)}</td>
                    <td>{parseFloat(conv.factor || 0).toFixed(4)}</td>
                    <td><span className={`status-badge ${conv.is_active ? 'status-completed' : 'status-pending'}`}>{conv.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteConversion(conv.id)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
