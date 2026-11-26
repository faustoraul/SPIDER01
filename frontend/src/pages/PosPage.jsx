import { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function PosPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [branches, setBranches] = useState([]);
  const [branchId, setBranchId] = useState('');
  
  // Estado de la Caja
  const [registers, setRegisters] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [openAmount, setOpenAmount] = useState('500.00');
  const [closeAmount, setCloseAmount] = useState('');
  
  // Estado de la Venta
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [customerId, setCustomerId] = useState('');
  const [customers, setCustomers] = useState([]);
  const [payMethod, setPayMethod] = useState('cash');
  const [error, setError] = useState(null);

  // Cargar empresas
  useEffect(() => {
    api.get('/companies').then(list => {
      setCompanies(list);
      if (list.length > 0) setCompanyId(String(list[0].id));
    }).catch(err => setError(err.message));
  }, []);

  // Cargar sucursales, clientes, productos y cajas al cambiar empresa
  useEffect(() => {
    if (!companyId) return;
    Promise.all([
      api.get(`/companies/${companyId}/branches`),
      api.get(`/companies/${companyId}/customers`),
      api.get(`/companies/${companyId}/products`),
      api.get(`/companies/${companyId}/cash-registers`)
    ]).then(([brData, custData, prodData, regData]) => {
      setBranches(brData);
      setCustomers(custData.items);
      setProducts(prodData.items);
      setRegisters(regData);
      if (brData.length > 0) setBranchId(String(brData[0].id));
    }).catch(err => setError(err.message));
  }, [companyId]);

  // Revisar si hay una caja abierta para la sucursal seleccionada
  useEffect(() => {
    if (!companyId) return;
    api.get(`/companies/${companyId}/cash-sessions?status=open`).then(res => {
      const session = res.items.find(s => s.cash_register_id === registers.find(r => r.branch_id === parseInt(branchId))?.id);
      setActiveSession(session || null);
    }).catch(err => console.error(err));
  }, [companyId, branchId, registers]);

  // --- Lógica de Caja ---
  const openCash = async () => {
    const reg = registers.find(r => r.branch_id === parseInt(branchId));
    if (!reg) return setError('No hay caja registradora en esta sucursal.');
    try {
      const session = await api.post(`/companies/${companyId}/cash-sessions`, {
        cash_register_id: reg.id,
        user_name: 'Cajero Web',
        opening_amount: parseFloat(openAmount)
      });
      setActiveSession(session);
    } catch (err) { setError(err.message); }
  };

  const closeCash = async () => {
    if (!activeSession) return;
    try {
      const closed = await api.post(`/companies/${companyId}/cash-sessions/${activeSession.id}/close`, {
        closing_amount: parseFloat(closeAmount),
        notes: 'Cierre desde POS Web'
      });
      alert(`Caja cerrada. Diferencia: $${closed.difference.toFixed(2)}`);
      setActiveSession(null);
      setCloseAmount('');
    } catch (err) { setError(err.message); }
  };

  // --- Lógica de Carrito ---
  const addToCart = (product) => {
    const existing = cart.find(item => item.product_id === product.id);
    if (existing) {
      setCart(cart.map(item => item.product_id === product.id ? { ...item, quantity: item.quantity + 1 } : item));
    } else {
      setCart([...cart, { product_id: product.id, name: product.name, price: product.sale_price, quantity: 1, tax_rate: product.tax_rate }]);
    }
  };

  const updateQty = (productId, delta) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty } : null;
      }
      return item;
    }).filter(Boolean));
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let tax = 0;
    cart.forEach(item => {
      const line = item.price * item.quantity;
      subtotal += line;
      tax += line * (item.tax_rate / 100);
    });
    return { subtotal, tax, total: subtotal + tax };
  };

  const totalToPay = calculateTotals().total;

  // --- Cobrar ---
  const checkout = async () => {
    if (cart.length === 0) return setError('El carrito está vacío.');
    if (!activeSession) return setError('Debes abrir la caja antes de vender.');
    setError(null);
    try {
      const payload = {
        branch_id: parseInt(branchId),
        customer_id: customerId ? parseInt(customerId) : null,
        sale_number: `POS-${Date.now()}`,
        issue_date: new Date().toISOString().slice(0, 10),
        items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.price, tax_rate: i.tax_rate, discount: 0 })),
        payments: [{ method: payMethod, amount: totalToPay }]
      };
      await api.post(`/companies/${companyId}/sales`, payload);
      alert('Venta realizada con éxito');
      setCart([]);
    } catch (err) { setError(err.message); }
  };

  const filteredProducts = products.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) || p.sku.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', background: '#f0f0f0', padding: '1rem', borderRadius: 6 }}>
        <select value={companyId} onChange={e => setCompanyId(e.target.value)} style={input}>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={branchId} onChange={e => setBranchId(e.target.value)} style={input}>
          {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        {!activeSession ? (
          <>
            <input type="number" value={openAmount} onChange={e => setOpenAmount(e.target.value)} placeholder="Fondo inicial" style={{...input, width: 100}} />
            <button onClick={openCash} style={{...btn, background: '#0d6efd', color: '#fff'}}>Abrir Caja</button>
          </>
        ) : (
          <>
            <span style={{ padding: '6px', color: '#198754', fontWeight: 'bold' }}>Caja Abierta</span>
            <input type="number" value={closeAmount} onChange={e => setCloseAmount(e.target.value)} placeholder="Monto cierre" style={{...input, width: 100}} />
            <button onClick={closeCash} style={{...btn, background: '#dc3545', color: '#fff'}}>Cerrar Caja</button>
          </>
        )}
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
        {/* Panel Izquierdo: Productos */}
        <div>
          <input type="text" placeholder="Buscar producto por nombre o SKU..." value={search} onChange={e => setSearch(e.target.value)} style={{...input, width: '100%', marginBottom: '1rem'}} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.5rem' }}>
            {filteredProducts.map(p => (
              <div key={p.id} onClick={() => addToCart(p)} style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '1rem', cursor: 'pointer', textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                <strong style={{ display: 'block', fontSize: 13 }}>{p.name}</strong>
                <span style={{ color: '#666', fontSize: 12 }}>SKU: {p.sku}</span>
                <div style={{ fontSize: 18, color: '#198754', marginTop: 4 }}>${p.sale_price.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Panel Derecho: Carrito */}
        <div style={{ background: '#f8f9fa', border: '1px solid #ddd', borderRadius: 6, padding: '1rem', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginTop: 0 }}>Carrito</h3>
          <select value={customerId} onChange={e => setCustomerId(e.target.value)} style={{...input, width: '100%', marginBottom: '1rem'}}>
            <option value="">Consumidor Final</option>
            {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          
          <div style={{ flex: 1, minHeight: 200, marginBottom: '1rem' }}>
            {cart.map(item => (
              <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #eee', padding: '0.5rem 0', fontSize: 13 }}>
                <div>
                  <strong>{item.name}</strong>
                  <div>${item.price.toFixed(2)} x {item.quantity}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <button onClick={() => updateQty(item.product_id, -1)} style={btn}>-</button>
                  <span>{item.quantity}</span>
                  <button onClick={() => updateQty(item.product_id, 1)} style={btn}>+</button>
                </div>
              </div>
            ))}
          </div>

          <div style={{ borderTop: '2px solid #333', paddingTop: '0.5rem', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Subtotal:</span><span>${calculateTotals().subtotal.toFixed(2)}</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>ITBIS:</span><span>${calculateTotals().tax.toFixed(2)}</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 20, fontWeight: 'bold', marginTop: 4 }}><span>Total:</span><span>${totalToPay.toFixed(2)}</span></div>
          </div>

          <select value={payMethod} onChange={e => setPayMethod(e.target.value)} style={{...input, width: '100%', marginBottom: '0.5rem'}}>
            <option value="cash">Efectivo</option>
            <option value="card">Tarjeta</option>
            <option value="transfer">Transferencia</option>
          </select>

          <button onClick={checkout} disabled={cart.length === 0 || !activeSession} style={{ padding: '1rem', background: cart.length > 0 && activeSession ? '#198754' : '#ccc', color: '#fff', border: 'none', borderRadius: 6, fontSize: 16, fontWeight: 'bold', cursor: 'pointer' }}>
            Cobrar ${totalToPay.toFixed(2)}
          </button>
        </div>
      </div>
    </>
  );
}

const input = { padding: '8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { padding: '4px 8px', border: '1px solid #999', background: '#fff', borderRadius: 4, cursor: 'pointer' };