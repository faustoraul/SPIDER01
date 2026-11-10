import { useEffect, useState } from 'react';
import { api } from '../services/api';

const emptyProductForm = {
  sku: '',
  barcode: '',
  name: '',
  description: '',
  category_id: '',
  brand_id: '',
  unit_measure: 'unit',
  cost_price: '',
  sale_price: '',
  tax_rate: '18',
  min_stock_alert: '0',
};

const emptyMovementForm = {
  product_id: '',
  movement_type: 'in',
  quantity: '',
  reference: '',
  notes: '',
};

export default function InventoryPage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [branches, setBranches] = useState([]);
  const [branchId, setBranchId] = useState('');
  const [products, setProducts] = useState([]);
  const [stock, setStock] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState(null);

  const [showProductForm, setShowProductForm] = useState(false);
  const [productForm, setProductForm] = useState(emptyProductForm);

  const [showMovementForm, setShowMovementForm] = useState(false);
  const [movementForm, setMovementForm] = useState(emptyMovementForm);

  useEffect(() => {
    api.get('/companies')
      .then((list) => {
        setCompanies(list);
        if (list.length > 0) setCompanyId(String(list[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!companyId) return;
    Promise.all([
      api.get(`/companies/${companyId}/branches`),
      api.get(`/companies/${companyId}/categories`),
      api.get(`/companies/${companyId}/brands`),
    ]).then(([branchesData, catsData, brandsData]) => {
      setBranches(branchesData);
      setCategories(catsData);
      setBrands(brandsData);
      if (branchesData.length > 0) setBranchId(String(branchesData[0].id));
    }).catch((err) => setError(err.message));
  }, [companyId]);

  const loadData = async () => {
    if (!companyId) return;
    try {
      const qs = search ? `?search=${encodeURIComponent(search)}` : '';
      const productsData = await api.get(`/companies/${companyId}/products${qs}`);
      setProducts(productsData.items);

      if (branchId) {
        const stockData = await api.get(`/companies/${companyId}/branches/${branchId}/inventory`);
        setStock(stockData);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [companyId, branchId, search]);

  const stockFor = (productId) => {
    const entry = stock.find((s) => s.product_id === productId);
    return entry || { quantity: 0, is_low_stock: false };
  };

  const resetProductForm = () => {
    setProductForm(emptyProductForm);
    setShowProductForm(false);
  };

  const submitProduct = async (ev) => {
    ev.preventDefault();
    setError(null);
    try {
      await api.post(`/companies/${companyId}/products`, {
        sku: productForm.sku,
        barcode: productForm.barcode || null,
        name: productForm.name,
        description: productForm.description || null,
        category_id: productForm.category_id ? parseInt(productForm.category_id, 10) : null,
        brand_id: productForm.brand_id ? parseInt(productForm.brand_id, 10) : null,
        unit_measure: productForm.unit_measure,
        cost_price: parseFloat(productForm.cost_price) || 0,
        sale_price: parseFloat(productForm.sale_price) || 0,
        tax_rate: parseFloat(productForm.tax_rate) || 0,
        min_stock_alert: parseInt(productForm.min_stock_alert, 10) || 0,
      });
      resetProductForm();
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const openMovementForm = (product) => {
    setMovementForm({ ...emptyMovementForm, product_id: String(product.id) });
    setShowMovementForm(true);
  };

  const submitMovement = async (ev) => {
    ev.preventDefault();
    setError(null);
    try {
      await api.post(`/companies/${companyId}/inventory/movements`, {
        branch_id: parseInt(branchId, 10),
        product_id: parseInt(movementForm.product_id, 10),
        movement_type: movementForm.movement_type,
        quantity: parseFloat(movementForm.quantity),
        reference: movementForm.reference || null,
        notes: movementForm.notes || null,
      });
      setMovementForm(emptyMovementForm);
      setShowMovementForm(false);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <select value={branchId} onChange={(e) => setBranchId(e.target.value)} style={input}>
          {branches.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Buscar por nombre o SKU..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ ...input, flex: 1, minWidth: 200 }}
        />
        <button
          onClick={() => setShowProductForm(true)}
          style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
        >
          + Nuevo Producto
        </button>
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      {showProductForm && (
        <form onSubmit={submitProduct} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
          <h3 style={{ marginTop: 0 }}>Nuevo Producto</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
            <Field label="SKU *">
              <input required value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} style={input} />
            </Field>
            <Field label="Código de barras">
              <input value={productForm.barcode} onChange={(e) => setProductForm({ ...productForm, barcode: e.target.value })} style={input} />
            </Field>
            <Field label="Nombre *">
              <input required value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} style={input} />
            </Field>
            <Field label="Categoría">
              <select value={productForm.category_id} onChange={(e) => setProductForm({ ...productForm, category_id: e.target.value })} style={input}>
                <option value="">Sin categoría</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </Field>
            <Field label="Marca">
              <select value={productForm.brand_id} onChange={(e) => setProductForm({ ...productForm, brand_id: e.target.value })} style={input}>
                <option value="">Sin marca</option>
                {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </Field>
            <Field label="Unidad de medida">
              <select value={productForm.unit_measure} onChange={(e) => setProductForm({ ...productForm, unit_measure: e.target.value })} style={input}>
                <option value="unit">Unidad</option>
                <option value="kg">Kilogramo</option>
                <option value="lt">Litro</option>
                <option value="box">Caja</option>
              </select>
            </Field>
            <Field label="Costo">
              <input type="number" step="0.01" value={productForm.cost_price} onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })} style={input} />
            </Field>
            <Field label="Precio venta">
              <input type="number" step="0.01" value={productForm.sale_price} onChange={(e) => setProductForm({ ...productForm, sale_price: e.target.value })} style={input} />
            </Field>
            <Field label="Impuesto (%)">
              <input type="number" step="0.01" value={productForm.tax_rate} onChange={(e) => setProductForm({ ...productForm, tax_rate: e.target.value })} style={input} />
            </Field>
            <Field label="Alerta stock mínimo">
              <input type="number" value={productForm.min_stock_alert} onChange={(e) => setProductForm({ ...productForm, min_stock_alert: e.target.value })} style={input} />
            </Field>
            <Field label="Descripción" full>
              <textarea value={productForm.description} onChange={(e) => setProductForm({ ...productForm, description: e.target.value })} style={{ ...input, minHeight: 50 }} />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>Crear producto</button>
            <button type="button" onClick={resetProductForm} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
          </div>
        </form>
      )}

      {showMovementForm && (
        <form onSubmit={submitMovement} style={{ background: '#fff3cd', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ffc107' }}>
          <h3 style={{ marginTop: 0 }}>Registrar Movimiento</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
            <Field label="Tipo">
              <select value={movementForm.movement_type} onChange={(e) => setMovementForm({ ...movementForm, movement_type: e.target.value })} style={input}>
                <option value="in">Entrada (IN)</option>
                <option value="out">Salida (OUT)</option>
                <option value="adjustment">Ajuste absoluto</option>
              </select>
            </Field>
            <Field label="Cantidad *">
              <input required type="number" step="0.01" min="0" value={movementForm.quantity} onChange={(e) => setMovementForm({ ...movementForm, quantity: e.target.value })} style={input} />
            </Field>
            <Field label="Referencia">
              <input value={movementForm.reference} onChange={(e) => setMovementForm({ ...movementForm, reference: e.target.value })} style={input} placeholder="Ej: Factura #123" />
            </Field>
            <Field label="Notas" full>
              <input value={movementForm.notes} onChange={(e) => setMovementForm({ ...movementForm, notes: e.target.value })} style={input} />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#fd7e14', color: 'white', border: 'none', cursor: 'pointer' }}>Registrar</button>
            <button type="button" onClick={() => { setShowMovementForm(false); setMovementForm(emptyMovementForm); }} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
          </div>
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th style={th}>SKU</th>
            <th style={th}>Producto</th>
            <th style={th}>Categoría</th>
            <th style={th}>Marca</th>
            <th style={th}>Costo</th>
            <th style={th}>Venta</th>
            <th style={th}>Stock</th>
            <th style={th}>Alerta</th>
            <th style={th}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => {
            const stockInfo = stockFor(p.id);
            return (
              <tr key={p.id} style={stockInfo.is_low_stock ? { background: '#fff3f3' } : {}}>
                <td style={td}><code>{p.sku}</code></td>
                <td style={td}>{p.name}</td>
                <td style={td}>{p.category_name || '—'}</td>
                <td style={td}>{p.brand_name || '—'}</td>
                <td style={td}>${p.cost_price.toFixed(2)}</td>
                <td style={td}>${p.sale_price.toFixed(2)}</td>
                <td style={td}>
                  <strong style={{ color: stockInfo.is_low_stock ? '#dc3545' : '#198754' }}>
                    {stockInfo.quantity}
                  </strong>
                </td>
                <td style={td}>
                  {stockInfo.is_low_stock ? (
                    <span style={{ background: '#dc3545', color: 'white', padding: '2px 6px', borderRadius: 10, fontSize: '11px' }}>
                      BAJO (min {p.min_stock_alert})
                    </span>
                  ) : '—'}
                </td>
                <td style={td}>
                  <button onClick={() => openMovementForm(p)} style={btn}>Movimiento</button>
                </td>
              </tr>
            );
          })}
          {products.length === 0 && (
            <tr>
              <td colSpan={9} style={{ ...td, textAlign: 'center', color: '#888' }}>
                No hay productos. Crea uno nuevo o ejecuta <code>flask seed-inventory</code>.
              </td>
            </tr>
          )}
        </tbody>
      </table>
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

const th = { padding: 6, border: '1px solid #ccc', textAlign: 'left' };
const td = { padding: 6, border: '1px solid #ccc' };
const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };
const btn = { background: 'none', border: '1px solid #999', padding: '2px 8px', cursor: 'pointer', borderRadius: 3 };