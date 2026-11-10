import { useEffect, useState } from 'react';
import CompaniesPage from './pages/CompaniesPage';
import CustomersPage from './pages/CustomersPage';
import LeadsPage from './pages/LeadsPage';
import PipelinePage from './pages/PipelinePage';
import SocialPage from './pages/SocialPage';
import InventoryPage from './pages/InventoryPage';
import { api } from './services/api';

export default function App() {
  const [tab, setTab] = useState('companies');
  const [backendStatus, setBackendStatus] = useState('comprobando...');
  const [dbStatus, setDbStatus] = useState('...');

  useEffect(() => {
    let cancelled = false;
    api.get('/health')
      .then((health) => {
        if (cancelled) return;
        setBackendStatus(health.status === 'ok' ? 'conectado' : 'respuesta inesperada');
        setDbStatus(health.database || 'desconocido');
      })
      .catch(() => {
        if (!cancelled) setBackendStatus('sin conexión');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif', maxWidth: 1400, margin: '0 auto' }}>
      <h1 style={{ marginBottom: '0.25rem' }}>SPIDER</h1>
      <p style={{ color: '#666', marginTop: 0 }}>Fase 8 — Productos e Inventario</p>

      <div style={{ background: '#f0f0f0', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1.5rem' }}>
        <div>Backend: <strong>{backendStatus}</strong></div>
        <div>Base de datos: <strong>{dbStatus}</strong></div>
      </div>

      <div style={{ marginBottom: '1.25rem', borderBottom: '1px solid #ddd' }}>
        <button onClick={() => setTab('companies')} style={tabStyle(tab === 'companies')}>Empresas</button>
        <button onClick={() => setTab('customers')} style={tabStyle(tab === 'customers')}>Clientes</button>
        <button onClick={() => setTab('leads')} style={tabStyle(tab === 'leads')}>Leads</button>
        <button onClick={() => setTab('pipeline')} style={tabStyle(tab === 'pipeline')}>Pipeline</button>
        <button onClick={() => setTab('social')} style={tabStyle(tab === 'social')}>Redes Sociales</button>
        <button onClick={() => setTab('inventory')} style={tabStyle(tab === 'inventory')}>Inventario</button>
      </div>

      {tab === 'companies' && <CompaniesPage />}
      {tab === 'customers' && <CustomersPage />}
      {tab === 'leads' && <LeadsPage />}
      {tab === 'pipeline' && <PipelinePage />}
      {tab === 'social' && <SocialPage />}
      {tab === 'inventory' && <InventoryPage />}
    </div>
  );
}

function tabStyle(active) {
  return {
    padding: '0.5rem 1rem',
    border: 'none',
    background: active ? '#0d6efd' : 'transparent',
    color: active ? 'white' : '#333',
    cursor: 'pointer',
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
    marginRight: 4,
    fontSize: 14,
    fontWeight: active ? 'bold' : 'normal',
  };
}