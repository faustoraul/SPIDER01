import { useEffect, useState } from 'react';
import { api } from '../services/api';

const emptySupplierForm = { name: '', tax_id: '', email: '', phone: '', address: '' };
const emptyOrderForm = {
  supplier_id: '',
  branch_id: '',
  order_number: '',
  order_date: new Date().toISOString().slice(0, 10),
  expected_date: '',
  notes: '',
};

export default function PurchasesPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [activeTab, setActiveTab] = useState('orders'); // 'orders' | 'suppliers'

  const [suppliers, setSuppliers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [branches, setBranches] = useState([]);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);

  // Formularios
  const [showSupplierForm, setShowSupplierForm] = useState(false);
  const [supplierForm, setSupplierForm] = useState(emptySupplierForm);

  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderForm, setOrderForm] = useState(emptyOrderForm);
  const [orderItems, setOrderItems] = useState([{ product_id: '', quantity: 1, unit_cost: 0 }]);

  useEffect(() => {
    api.get('/companies')
      .then((list) => {
        setCompanies(list);
        if (list.length > 0) setCompanyId(String(list[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  const loadData = async () => {
    if (!companyId) return;
    try {
      const [supData, ordData, brData, prodData] = await Promise.all([
        api.get(`/companies/${companyId}/suppliers`),
        api.get(`/companies/${companyId}/purchase-orders`),
        api.get(`/companies/${companyId}/branches`),
        api.get(`/companies/${companyId}/products`),
      ]);
      setSuppliers(supData);
      setOrders(ordData.items);
      setBranches(brData);
      setProducts(prodData.items);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [companyId]);

  // --- Acciones Proveedores ---
  const submitSupplier = async (ev) => {
    ev.preventDefault();
    setError(null);
    try {
      await api.post(`/companies/${companyId}/suppliers`, supplierForm);
      setSupplierForm(emptySupplierForm);
      setShowSupplierForm(false);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  // --- Acciones Órdenes ---
  const addItemRow = () => {
    setOrderItems([...orderItems, { product_id: '', quantity: 1, unit_cost: 0 }]);
  };

  const removeItemRow = (index) => {
    setOrderItems(orderItems.filter((_, i) => i !== index));
  };

  const updateItemRow = (index, field, value) => {
    const newItems = [...orderItems];
    newItems[index][field] = value;
    setOrderItems(newItems);
  };

  const submitOrder = async (ev) => {
    ev.preventDefault();
    setError(null);
    const payload = {
      ...orderForm,
      supplier_id: parseInt(orderForm.supplier_id, 10),
      branch_id: parseInt(orderForm.branch_id, 10),
      expected_date: orderForm.expected_date || null,
      items: orderItems.map((i) => ({
        product_id: parseInt(i.product_id, 10),
        quantity: parseFloat(i.quantity),
        unit_cost: parseFloat(i.unit_cost),
      })),
    };

    try {
      await api.post(`/companies/${companyId}/purchase-orders`, payload);
      setOrderForm(emptyOrderForm);
      setOrderItems([{ product_id: '', quantity: 1, unit_cost: 0 }]);
      setShowOrderForm(false);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const receiveOrder = async (order) => {
    if (!window.confirm(`¿Recibir la orden ${order.order_number}? Esto sumará stock al inventario.`)) return;
    try {
      await api.post(`/companies/${companyId}/purchase-orders/${order.id}/receive`);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 0 }}>
          <button onClick={() => setActiveTab('orders')} style={tabStyle(activeTab === 'orders')}>Órdenes</button>
          <button onClick={() => setActiveTab('suppliers')} style={tabStyle(activeTab === 'suppliers')}>Proveedores</button>
        </div>
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      {/* --- VISTA: PROVEEDORES --- */}
      {activeTab === 'suppliers' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <button onClick={() => setShowSupplierForm(true)} style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
              + Nuevo Proveedor
            </button>
          </div>

          {showSupplierForm && (
            <form onSubmit={submitSupplier} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
              <h3 style={{ marginTop: 0 }}>Nuevo Proveedor</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                <Field label="Nombre *"><input required value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} style={input} /></Field>
                <Field label="RNC / Tax ID"><input value={supplierForm.tax_id} onChange={(e) => setSupplierForm({ ...supplierForm, tax_id: e.target.value })} style={input} /></Field>
                <Field label="Email"><input type="email" value={supplierForm.email} onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })} style={input} /></Field>
                <Field label="Teléfono"><input value={supplierForm.phone} onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })} style={input} /></Field>
                <Field label="Dirección" full><input value={supplierForm.address} onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })} style={input} /></Field>
              </div>
              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>Crear</button>
                <button type="button" onClick={() => setShowSupplierForm(false)} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
              </div>
            </form>
          )}

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead><tr style={{ background: '#eee' }}><th style={th}>ID</th><th style={th}>Nombre</th><th style={th}>Email</th><th style={th}>Teléfono</th></tr></thead>
            <tbody>
              {suppliers.map(s => (
                <tr key={s.id}>
                  <td style={td}>{s.id}</td><td style={td}>{s.name}</td><td style={td}>{s.email || '—'}</td><td style={td}>{s.phone || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* --- VISTA: ÓRDENES --- */}
      {activeTab === 'orders' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <button onClick={() => setShowOrderForm(true)} style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }} disabled={suppliers.length === 0 || branches.length === 0}>
              + Nueva Orden de Compra
            </button>
            {suppliers.length === 0 && <span style={{ marginLeft: 10, fontSize: 12, color: 'crimson' }}>Crea un proveedor primero.</span>}
          </div>

          {showOrderForm && (
            <form onSubmit={submitOrder} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
              <h3 style={{ marginTop: 0 }}>Nueva Orden</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                <Field label="Proveedor *">
                  <select required value={orderForm.supplier_id} onChange={(e) => setOrderForm({ ...orderForm, supplier_id: e.target.value })} style={input}>
                    <option value="">Seleccionar...</option>
                    {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </Field>
                <Field label="Sucursal destino *">
                  <select required value={orderForm.branch_id} onChange={(e) => setOrderForm({ ...orderForm, branch_id: e.target.value })} style={input}>
                    <option value="">Seleccionar...</option>
                    {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </Field>
                <Field label="Nº Orden *"><input required value={orderForm.order_number} onChange={(e) => setOrderForm({ ...orderForm, order_number: e.target.value })} style={input} placeholder="PO-2026-002" /></Field>
                <Field label="Fecha Orden *"><input type="date" required value={orderForm.order_date} onChange={(e) => setOrderForm({ ...orderForm, order_date: e.target.value })} style={input} /></Field>
              </div>

              <h4>Ítems</h4>
              <table style={{ width: '100%', marginBottom: '1rem', fontSize: 13 }}>
                <thead><tr style={{ background: '#e9ecef' }}><th style={th}>Producto</th><th style={th}>Cantidad</th><th style={th}>Costo Unit.</th><th style={th}>Subtotal</th><th style={th}></th></tr></thead>
                <tbody>
                  {orderItems.map((item, index) => {
                    const prod = products.find(p => p.id === parseInt(item.product_id));
                    const subtotal = (item.quantity || 0) * (item.unit_cost || 0);
                    return (
                      <tr key={index}>
                        <td style={td}>
                          <select required value={item.product_id} onChange={(e) => updateItemRow(index, 'product_id', e.target.value)} style={{ ...input, width: '100%' }}>
                            <option value="">Seleccionar...</option>
                            {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                          </select>
                        </td>
                        <td style={td}><input type="number" min="1" required value={item.quantity} onChange={(e) => updateItemRow(index, 'quantity', e.target.value)} style={{ ...input, width: 80 }} /></td>
                        <td style={td}><input type="number" step="0.01" min="0" required value={item.unit_cost} onChange={(e) => updateItemRow(index, 'unit_cost', e.target.value)} style={{ ...input, width: 100 }} /></td>
                        <td style={td}>${subtotal.toFixed(2)}</td>
                        <td style={td}><button type="button" onClick={() => removeItemRow(index)} style={{ ...btn, color: 'crimson' }}>X</button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <button type="button" onClick={addItemRow} style={{ ...btn, marginBottom: '1rem' }}>+ Añadir ítem</button>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>Crear Orden</button>
                <button type="button" onClick={() => setShowOrderForm(false)} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
              </div>
            </form>
          )}

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead><tr style={{ background: '#eee' }}><th style={th}>Nº Orden</th><th style={th}>Proveedor</th><th style={th}>Fecha</th><th style={th}>Total</th><th style={th}>Estado</th><th style={th}>Acciones</th></tr></thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id}>
                  <td style={td}><strong>{o.order_number}</strong></td>
                  <td style={td}>{o.supplier_name}</td>
                  <td style={td}>{o.order_date}</td>
                  <td style={td}>${o.total.toFixed(2)}</td>
                  <td style={td}>
                    <span style={{ padding: '2px 6px', borderRadius: 10, fontSize: 11, fontWeight: 'bold', color: 'white', background: o.status === 'received' ? '#198754' : (o.status === 'ordered' ? '#fd7e14' : '#6c757d') }}>
                      {o.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={td}>
                    {o.status !== 'received' && o.status !== 'cancelled' && (
                      <button onClick={() => receiveOrder(o)} style={{ ...btn, background: '#d1e7dd', borderColor: '#198754', color: '#0f5132' }}>Recibir Mercancía</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Field({ label, children, full }) {
  return (
    <label style={{ gridColumn: full ? '1 / -1' : 'auto', display: 'flex', flexDirection: 'column', fontSize: 13 }}>
      <span style={{ marginBottom: 2, fontWeight: 'bold' }}>{label}</span>
      {children}
    </label>
  );
}

const th = { padding: 8, border: '1px solid #ccc', textAlign: 'left' };
const td = { padding: 8, border: '1px solid #ccc' };
const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { background: 'none', border: '1px solid #999', padding: '4px 8px', cursor: 'pointer', borderRadius: 3 };

function tabStyle(active) {
  return {
    padding: '0.5rem 1rem',
    border: 'none',
    background: active ? '#333' : '#e0e0e0',
    color: active ? 'white' : '#333',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: active ? 'bold' : 'normal',
    marginLeft: 4,
  };
}