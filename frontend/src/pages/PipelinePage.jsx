import { useEffect, useState } from 'react';
import { api } from '../services/api';

const emptyForm = {
  customer_id: '',
  stage_id: '',
  name: '',
  amount: '',
  expected_close_date: '',
  notes: '',
};

export default function PipelinePage() {
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState('');
  const [stages, setStages] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

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
      const [stagesData, oppsData, customersData] = await Promise.all([
        api.get(`/companies/${companyId}/pipeline/stages`),
        api.get(`/companies/${companyId}/pipeline/opportunities`),
        api.get(`/companies/${companyId}/customers`),
      ]);
      setStages(stagesData);
      setOpportunities(oppsData.items);
      setCustomers(customersData.items);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [companyId]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
    setError(null);
  };

  const openNewForm = (presetStageId = '') => {
    setForm({
      ...emptyForm,
      customer_id: customers.length > 0 ? String(customers[0].id) : '',
      stage_id: presetStageId || (stages.length > 0 ? String(stages[0].id) : ''),
    });
    setEditingId(null);
    setShowForm(true);
  };

  const openEditForm = (opp) => {
    setForm({
      customer_id: String(opp.customer_id),
      stage_id: String(opp.stage_id),
      name: opp.name,
      amount: String(opp.amount),
      expected_close_date: opp.expected_close_date || '',
      notes: opp.notes || '',
    });
    setEditingId(opp.id);
    setShowForm(true);
  };

  const submitForm = async (ev) => {
    ev.preventDefault();
    setError(null);
    const payload = {
      customer_id: parseInt(form.customer_id, 10),
      stage_id: parseInt(form.stage_id, 10),
      name: form.name,
      amount: parseFloat(form.amount) || 0,
      expected_close_date: form.expected_close_date || null,
      notes: form.notes || null,
    };
    try {
      if (editingId) {
        await api.put(`/companies/${companyId}/pipeline/opportunities/${editingId}`, payload);
      } else {
        await api.post(`/companies/${companyId}/pipeline/opportunities`, payload);
      }
      resetForm();
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const moveStage = async (opp, newStageId) => {
    try {
      await api.patch(`/companies/${companyId}/pipeline/opportunities/${opp.id}`, {
        stage_id: parseInt(newStageId, 10),
      });
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const softDelete = async (opp) => {
    if (!window.confirm(`¿Dar de baja la oportunidad "${opp.name}"?`)) return;
    try {
      await api.del(`/companies/${companyId}/pipeline/opportunities/${opp.id}`);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const oppsByStage = (stageId) => opportunities.filter((o) => o.stage_id === stageId);

  const totalByStage = (stageId) =>
    oppsByStage(stageId).reduce((sum, o) => sum + (o.amount || 0), 0);

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={input}>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <button
          onClick={() => openNewForm()}
          style={{ ...input, background: '#0d6efd', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
          disabled={customers.length === 0}
        >
          + Nueva Oportunidad
        </button>
        {customers.length === 0 && (
          <span style={{ color: '#888', fontSize: 13 }}>Necesitas al menos un cliente para crear oportunidades.</span>
        )}
      </div>

      {error && <p style={{ color: 'crimson', fontWeight: 'bold' }}>Error: {error}</p>}

      {showForm && (
        <form onSubmit={submitForm} style={{ background: '#f6f8fa', padding: '1rem', borderRadius: 6, marginBottom: '1rem', border: '1px solid #ddd' }}>
          <h3 style={{ marginTop: 0 }}>{editingId ? 'Editar oportunidad' : 'Nueva oportunidad'}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
            <Field label="Nombre *">
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={input} />
            </Field>
            <Field label="Cliente *">
              <select required value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} style={input}>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Etapa *">
              <select required value={form.stage_id} onChange={(e) => setForm({ ...form, stage_id: e.target.value })} style={input}>
                {stages.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Monto">
              <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} style={input} />
            </Field>
            <Field label="Fecha estimada de cierre">
              <input type="date" value={form.expected_close_date} onChange={(e) => setForm({ ...form, expected_close_date: e.target.value })} style={input} />
            </Field>
            <Field label="Notas" full>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} style={{ ...input, minHeight: 60 }} />
            </Field>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" style={{ ...input, background: '#198754', color: 'white', border: 'none', cursor: 'pointer' }}>
              {editingId ? 'Guardar cambios' : 'Crear oportunidad'}
            </button>
            <button type="button" onClick={resetForm} style={{ ...input, cursor: 'pointer' }}>Cancelar</button>
          </div>
        </form>
      )}

      {stages.length === 0 ? (
        <p style={{ color: '#888' }}>No hay etapas configuradas para esta empresa.</p>
      ) : (
        <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '1rem' }}>
          {stages.map((stage) => {
            const items = oppsByStage(stage.id);
            const total = totalByStage(stage.id);
            return (
              <div
                key={stage.id}
                style={{
                  minWidth: 240, flex: '0 0 240px', background: '#f8f9fa',
                  border: '1px solid #dee2e6', borderRadius: 8, padding: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, padding: '0 4px' }}>
                  <strong style={{ fontSize: 13 }}>{stage.name}</strong>
                  <span style={{ fontSize: 11, color: '#666' }}>{items.length}</span>
                </div>
                <div style={{ fontSize: 11, color: '#666', marginBottom: 6, padding: '0 4px' }}>
                  ${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {items.map((opp) => (
                    <div
                      key={opp.id}
                      style={{
                        background: 'white', border: '1px solid #e0e0e0',
                        borderRadius: 6, padding: 8, fontSize: 12,
                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: 2 }}>{opp.name}</div>
                      <div style={{ color: '#666', marginBottom: 4 }}>{opp.customer_name}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#198754', fontWeight: 'bold' }}>
                          ${(opp.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                        {opp.expected_close_date && (
                          <span style={{ color: '#888', fontSize: 10 }}>{opp.expected_close_date}</span>
                        )}
                      </div>
                      <div style={{ marginTop: 6, display: 'flex', gap: 4, alignItems: 'center' }}>
                        <select
                          value={opp.stage_id}
                          onChange={(e) => moveStage(opp, e.target.value)}
                          style={{ fontSize: 10, padding: '2px 4px', border: '1px solid #ccc', borderRadius: 3, flex: 1 }}
                        >
                          {stages.map((s) => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => openEditForm(opp)}
                          title="Editar"
                          style={{ background: 'none', border: '1px solid #ccc', borderRadius: 3, cursor: 'pointer', padding: '1px 5px', fontSize: 10 }}
                        >
                          ✎
                        </button>
                        <button
                          onClick={() => softDelete(opp)}
                          title="Baja"
                          style={{ background: 'none', border: '1px solid #ccc', borderRadius: 3, cursor: 'pointer', padding: '1px 5px', fontSize: 10, color: 'crimson' }}
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                  {items.length === 0 && (
                    <div style={{ color: '#aaa', fontSize: 11, textAlign: 'center', padding: '12px 0' }}>Vacío</div>
                  )}
                </div>
              </div>
            );
          })}
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

const input = { padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4, font: 'inherit' };