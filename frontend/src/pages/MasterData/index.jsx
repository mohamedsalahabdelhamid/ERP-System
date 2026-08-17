import { useState, useEffect } from 'react';
import { getItems, createItem, updateItem, deleteItem, getCategories, createCategory, deleteCategory, getUnits, createUnit, deleteUnit, getUnitConversions, createUnitConversion, deleteUnitConversion } from '../../api/client';
import { useTranslation } from '../../contexts/TranslationContext';

export default function MasterData() {
  const { t } = useTranslation();
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
    if (!window.confirm(t('masterdata.delete_item'))) return;
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
    if (!window.confirm(t('masterdata.delete_category'))) return;
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
    if (!window.confirm(t('masterdata.delete_unit'))) return;
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
    if (!window.confirm(t('masterdata.delete_conversion'))) return;
    try { await deleteUnitConversion(id); fetchData(); }
    catch (err) { alert(err.response?.data?.detail || 'Error'); }
  };

  return (
    <div>
      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'items' ? 'active' : ''}`} onClick={() => setTab('items')}>{t('masterdata.tab_items')}</button>
        <button className={`tab-btn ${tab === 'categories' ? 'active' : ''}`} onClick={() => setTab('categories')}>{t('masterdata.tab_categories')}</button>
        <button className={`tab-btn ${tab === 'units' ? 'active' : ''}`} onClick={() => setTab('units')}>{t('masterdata.tab_units')}</button>
        <button className={`tab-btn ${tab === 'conversions' ? 'active' : ''}`} onClick={() => setTab('conversions')}>{t('masterdata.tab_conversions')}</button>
      </div>

      {tab === 'items' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => { setEditingId(null); resetItemForm(); setShowForm(!showForm); }}>{t('masterdata.add_item')}</button>
          </div>

          {showForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{editingId ? t('masterdata.edit_item') : t('masterdata.new_item')}</h3>
              <form onSubmit={handleSaveItem}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('masterdata.item_name')}</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('masterdata.item_code')}</label><input value={form.code} onChange={e => setForm({...form, code: e.target.value})} placeholder={t('common.auto_code_hint')} /></div>
                  <div className="form-group">
                    <label>{t('masterdata.type')}</label>
                    <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                      <option value="stock">{t('masterdata.stock')}</option>
                      <option value="service">{t('masterdata.service')}</option>
                      <option value="manufactured">{t('masterdata.manufactured')}</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>{t('masterdata.category')}</label>
                    <select value={form.item_category_id} onChange={e => setForm({...form, item_category_id: e.target.value})}>
                      <option value="">{t('common.select')}</option>
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>{t('masterdata.base_unit')}</label>
                    <select value={form.base_unit_id} onChange={e => setForm({...form, base_unit_id: e.target.value})}>
                      <option value="">{t('common.select')}</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>{t('masterdata.sale_price')}</label><input type="number" step="0.01" value={form.default_sale_price} onChange={e => setForm({...form, default_sale_price: e.target.value})} /></div>
                  <div className="form-group"><label>{t('masterdata.purchase_price')}</label><input type="number" step="0.01" value={form.default_purchase_price} onChange={e => setForm({...form, default_purchase_price: e.target.value})} /></div>
                  <div className="form-group"><label>{t('masterdata.min_stock')}</label><input type="number" step="0.01" value={form.min_stock_level} onChange={e => setForm({...form, min_stock_level: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('common.saving') : t('masterdata.save_item')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowForm(false); setEditingId(null); }}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('masterdata.code')}</th><th>{t('masterdata.name')}</th><th>{t('masterdata.category')}</th><th>{t('masterdata.type')}</th><th>{t('masterdata.sale_price')}</th><th>{t('masterdata.cost_price')}</th><th>{t('masterdata.min_stock_col')}</th><th></th></tr></thead>
              <tbody>
                {items.length === 0 ? <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('masterdata.no_items')}</td></tr>
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
                        <button className="btn" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => startEditItem(item)}>{t('masterdata.edit')}</button>
                        <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteItem(item.id)}>{t('masterdata.delete')}</button>
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
            <button className="btn btn-primary" onClick={() => setShowCatForm(!showCatForm)}>{t('masterdata.add_category')}</button>
          </div>
          {showCatForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('masterdata.new_category')}</h3>
              <form onSubmit={handleSaveCategory}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('masterdata.category_name')}</label><input value={catForm.name} onChange={e => setCatForm({...catForm, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('masterdata.code')}</label><input value={catForm.code} onChange={e => setCatForm({...catForm, code: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">{t('masterdata.save_category')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowCatForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('masterdata.category_name')}</th><th>{t('masterdata.code')}</th><th>{t('masterdata.status')}</th><th></th></tr></thead>
              <tbody>
                {categories.length === 0 ? <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('masterdata.no_categories')}</td></tr>
                : categories.map((c, i) => (
                  <tr key={c.id}>
                    <td>{i + 1}</td>
                    <td>{c.name}</td>
                    <td>{c.code}</td>
                    <td><span className={`status-badge ${c.is_active ? 'status-completed' : 'status-pending'}`}>{c.is_active ? t('masterdata.active') : t('masterdata.inactive')}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteCategory(c.id)}>{t('masterdata.delete')}</button></td>
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
            <button className="btn btn-primary" onClick={() => setShowUnitForm(!showUnitForm)}>{t('masterdata.add_unit')}</button>
          </div>
          {showUnitForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('masterdata.new_unit')}</h3>
              <form onSubmit={handleSaveUnit}>
                <div className="form-grid">
                  <div className="form-group"><label>{t('masterdata.unit_name')}</label><input value={unitForm.name} onChange={e => setUnitForm({...unitForm, name: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('masterdata.code')}</label><input value={unitForm.code} onChange={e => setUnitForm({...unitForm, code: e.target.value})} required /></div>
                  <div className="form-group"><label>{t('masterdata.symbol')}</label><input value={unitForm.symbol} onChange={e => setUnitForm({...unitForm, symbol: e.target.value})} /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">{t('masterdata.save_unit')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowUnitForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('masterdata.unit_name')}</th><th>{t('masterdata.code')}</th><th>{t('masterdata.symbol')}</th><th>{t('masterdata.status')}</th><th></th></tr></thead>
              <tbody>
                {units.length === 0 ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('masterdata.no_units')}</td></tr>
                : units.map((u, i) => (
                  <tr key={u.id}>
                    <td>{i + 1}</td>
                    <td>{u.name}</td>
                    <td>{u.code}</td>
                    <td>{u.symbol || '-'}</td>
                    <td><span className={`status-badge ${u.is_active ? 'status-completed' : 'status-pending'}`}>{u.is_active ? t('masterdata.active') : t('masterdata.inactive')}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteUnit(u.id)}>{t('masterdata.delete')}</button></td>
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
            <button className="btn btn-primary" onClick={() => setShowConvForm(!showConvForm)}>{t('masterdata.add_conversion')}</button>
          </div>
          {showConvForm && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1.5rem' }}>{t('masterdata.new_conversion')}</h3>
              <form onSubmit={handleSaveConversion}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>{t('masterdata.from_unit')}</label>
                    <select value={convForm.from_unit_id} onChange={e => setConvForm({...convForm, from_unit_id: e.target.value})} required>
                      <option value="">{t('common.select')}</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>{t('masterdata.to_unit')}</label>
                    <select value={convForm.to_unit_id} onChange={e => setConvForm({...convForm, to_unit_id: e.target.value})} required>
                      <option value="">{t('common.select')}</option>
                      {units.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>{t('masterdata.factor')}</label><input type="number" min="0" step="0.0001" value={convForm.factor} onChange={e => setConvForm({...convForm, factor: e.target.value})} required /></div>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">{t('masterdata.save_conversion')}</button>
                  <button type="button" className="btn" style={{ background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowConvForm(false)}>{t('common.cancel')}</button>
                </div>
              </form>
            </div>
          )}
          <div className="table-container">
            <table>
              <thead><tr><th>#</th><th>{t('masterdata.from_unit')}</th><th>{t('masterdata.to_unit')}</th><th>{t('masterdata.factor')}</th><th>{t('masterdata.status')}</th><th></th></tr></thead>
              <tbody>
                {conversions.length === 0 ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>{t('masterdata.no_conversions')}</td></tr>
                : conversions.map((conv, i) => (
                  <tr key={conv.id}>
                    <td>{i + 1}</td>
                    <td>{unitName(conv.from_unit_id)}</td>
                    <td>{unitName(conv.to_unit_id)}</td>
                    <td>{parseFloat(conv.factor || 0).toFixed(4)}</td>
                    <td><span className={`status-badge ${conv.is_active ? 'status-completed' : 'status-pending'}`}>{conv.is_active ? t('masterdata.active') : t('masterdata.inactive')}</span></td>
                    <td><button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleDeleteConversion(conv.id)}>{t('masterdata.delete')}</button></td>
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
