import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import UI components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { toast, Toaster } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('userData');
    if (token && userData) {
      setUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user_type, user_info } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('userData', JSON.stringify({ ...user_info, user_type }));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setUser({ ...user_info, user_type });
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error de conexión' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userData');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Login Component
function LoginPage() {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await login(formData.username, formData.password);
    if (!result.success) {
      toast.error(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center pb-8">
          <div className="mx-auto mb-4 w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
            <span className="text-white text-2xl font-bold">🏛️</span>
          </div>
          <CardTitle className="text-2xl font-bold text-gray-800">
            Sistema de Registro
          </CardTitle>
          <CardDescription className="text-gray-600">
            Bonos Gubernamentales de Panamá
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username">Usuario</Label>
              <Input
                id="username"
                type="text"
                placeholder="Ingrese su usuario"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                data-testid="login-username-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                placeholder="Ingrese su contraseña"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                data-testid="login-password-input"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              disabled={loading}
              data-testid="login-submit-button"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Admin Dashboard
function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [securities, setSecurities] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [newUser, setNewUser] = useState({ username: '', password: '', email: '', brokerage_name: '' });
  const [newSecurity, setNewSecurity] = useState({
    isin_code: '', latinex_code: '', security_description: '', 
    coupon: '', issue_date: '', maturity_date: ''
  });
  const [newAdmin, setNewAdmin] = useState({ username: '', password: '', email: '' });
  const [admins, setAdmins] = useState([]);
  const [importFile, setImportFile] = useState(null);
  const [editingSecurity, setEditingSecurity] = useState(null);
  const [editSecurityData, setEditSecurityData] = useState({
    isin_code: '', latinex_code: '', security_description: '', 
    coupon: '', issue_date: '', maturity_date: ''
  });
  const [editingUser, setEditingUser] = useState(null);
  const [editUserData, setEditUserData] = useState({
    username: '', email: '', brokerage_name: '', is_active: true, password: ''
  });
  const [showPasswordDialog, setShowPasswordDialog] = useState(null);
  const [showHoldingsDialog, setShowHoldingsDialog] = useState(null);
  const [userHoldings, setUserHoldings] = useState([]);
  const [editingHolding, setEditingHolding] = useState(null);
  const [newHoldingForUser, setNewHoldingForUser] = useState({
    filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
    legal_representative: '', amount_held: '', address: '', phone: '', email: ''
  });
  const [editHoldingData, setEditHoldingData] = useState({
    filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
    legal_representative: '', amount_held: '', address: '', phone: '', email: ''
  });
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    if (activeTab === 'users') loadUsers();
    if (activeTab === 'securities') loadSecurities();
    if (activeTab === 'holdings') loadHoldings();
    if (activeTab === 'admins') loadAdmins();
  }, [activeTab]);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      // Load users with holdings count
      const usersWithHoldings = await Promise.all(
        response.data.map(async (user) => {
          try {
            const holdingsResponse = await axios.get(`${API}/admin/users/${user.id}/holdings`);
            return { ...user, holdingsCount: holdingsResponse.data.length };
          } catch (error) {
            return { ...user, holdingsCount: 0 };
          }
        })
      );
      setUsers(usersWithHoldings);
    } catch (error) {
      toast.error('Error al cargar usuarios');
    }
  };

  const loadSecurities = async () => {
    try {
      const response = await axios.get(`${API}/admin/securities`);
      setSecurities(response.data);
    } catch (error) {
      toast.error('Error al cargar valores');
    }
  };

  const loadHoldings = async () => {
    try {
      const response = await axios.get(`${API}/admin/holdings`);
      setHoldings(response.data);
    } catch (error) {
      toast.error('Error al cargar tenencias');
    }
  };

  const loadAdmins = async () => {
    try {
      const response = await axios.get(`${API}/admin/admins`);
      setAdmins(response.data);
    } catch (error) {
      toast.error('Error al cargar administradores');
    }
  };

  const createUser = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/users`, newUser);
      setNewUser({ username: '', password: '', email: '', brokerage_name: '' });
      loadUsers();
      toast.success('Usuario creado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear usuario');
    }
    setLoading(false);
  };

  const createSecurity = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/securities`, newSecurity);
      setNewSecurity({ isin_code: '', latinex_code: '', security_description: '', coupon: '', issue_date: '', maturity_date: '' });
      loadSecurities();
      toast.success('Valor creado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear valor');
    }
    setLoading(false);
  };

  const createAdmin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/create-admin`, newAdmin);
      setNewAdmin({ username: '', password: '', email: '' });
      loadAdmins();
      toast.success('Administrador creado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear administrador');
    }
    setLoading(false);
  };

  const toggleUserStatus = async (userId) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/toggle`);
      loadUsers();
      toast.success('Estado del usuario actualizado');
    } catch (error) {
      toast.error('Error al actualizar usuario');
    }
  };

  const exportToExcel = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/export/excel`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tenencias_bonos_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Archivo exportado exitosamente');
    } catch (error) {
      toast.error('Error al exportar datos');
    }
    setLoading(false);
  };

  const importFromExcel = async () => {
    if (!importFile) {
      toast.error('Por favor seleccione un archivo');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', importFile);

      const response = await axios.post(`${API}/admin/import/excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;
      
      if (result.total_errors > 0) {
        // Show detailed error information
        const errorSummary = `${result.message}\n\nDetalles de errores:\n${result.errors.slice(0, 3).join('\n')}${result.errors.length > 3 ? '\n...' : ''}`;
        toast.error(`Importación con errores: ${result.imported_count} valores importados, ${result.total_errors} errores`, {
          description: result.errors.slice(0, 2).join('; '),
          duration: 8000
        });
        console.log('Errores detallados de importación:', result.errors);
      } else {
        toast.success(`¡Importación exitosa! ${result.imported_count} valores importados correctamente`);
      }
      
      // Refresh securities list and clear file
      loadSecurities();
      setImportFile(null);
      // Reset file input
      const fileInput = document.getElementById('excel-import');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al importar archivo');
    }
    setLoading(false);
  };

  const clearAllSecurities = async () => {
    const confirmed = window.confirm(
      '⚠️ ADVERTENCIA: Esta acción eliminará TODOS los valores registrados de la base de datos.\n\n' +
      'Esta operación NO se puede deshacer.\n\n' +
      '¿Está seguro que desea continuar?'
    );
    
    if (!confirmed) return;
    
    const doubleConfirm = window.confirm(
      '🚨 CONFIRMACIÓN FINAL\n\n' +
      'Está a punto de eliminar TODOS los valores registrados.\n\n' +
      'Haga clic en "Aceptar" para confirmar la eliminación permanente.'
    );
    
    if (!doubleConfirm) return;

    try {
      setLoading(true);
      const response = await axios.delete(`${API}/admin/securities/clear-all`);
      
      const result = response.data;
      toast.success(`✅ ${result.message}`, {
        description: `Se eliminaron ${result.deleted_count} valores de un total de ${result.total_before}`,
        duration: 5000
      });
      loadSecurities(); // Refresh the list
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al limpiar valores');
    }
    setLoading(false);
  };

  const startEditSecurity = (security) => {
    setEditingSecurity(security.id);
    setEditSecurityData({
      isin_code: security.isin_code || '',
      latinex_code: security.latinex_code || '',
      security_description: security.security_description || '',
      coupon: security.coupon || '',
      issue_date: security.issue_date || '',
      maturity_date: security.maturity_date || ''
    });
  };

  const cancelEditSecurity = () => {
    setEditingSecurity(null);
    setEditSecurityData({
      isin_code: '', latinex_code: '', security_description: '', 
      coupon: '', issue_date: '', maturity_date: ''
    });
  };

  const saveEditSecurity = async (securityId) => {
    setLoading(true);
    try {
      await axios.put(`${API}/admin/securities/${securityId}`, editSecurityData);
      setEditingSecurity(null);
      setEditSecurityData({
        isin_code: '', latinex_code: '', security_description: '', 
        coupon: '', issue_date: '', maturity_date: ''
      });
      loadSecurities();
      toast.success('Valor actualizado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar valor');
    }
    setLoading(false);
  };

  const deleteSecurity = async (securityId, description) => {
    const confirmed = window.confirm(
      `¿Está seguro que desea eliminar el valor?\n\n"${description}"\n\nEsta acción no se puede deshacer.`
    );
    
    if (!confirmed) return;

    try {
      setLoading(true);
      await axios.delete(`${API}/admin/securities/${securityId}`);
      loadSecurities();
      toast.success('Valor eliminado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar valor');
    }
    setLoading(false);
  };
  const startEditUser = (user) => {
    setEditingUser(user.id);
    setEditUserData({
      username: user.username || '',
      email: user.email || '',
      brokerage_name: user.brokerage_name || '',
      is_active: user.is_active,
      password: '' // Never pre-fill password
    });
  };

  const cancelEditUser = () => {
    setEditingUser(null);
    setEditUserData({
      username: '', email: '', brokerage_name: '', is_active: true, password: ''
    });
  };

  const saveEditUser = async (userId) => {
    setLoading(true);
    try {
      await axios.put(`${API}/admin/users/${userId}`, editUserData);
      setEditingUser(null);
      setEditUserData({
        username: '', email: '', brokerage_name: '', is_active: true, password: ''
      });
      loadUsers();
      toast.success('Usuario actualizado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar usuario');
    }
    setLoading(false);
  };

  const deleteUser = async (userId, username) => {
    const confirmed = window.confirm(
      `¿Está seguro que desea eliminar el usuario "${username}"?\n\nEsta acción eliminará permanentemente el usuario y no se puede deshacer.\n\nNOTA: Si el usuario tiene tenencias registradas, no se podrá eliminar.`
    );
    
    if (!confirmed) return;

    try {
      setLoading(true);
      await axios.delete(`${API}/admin/users/${userId}`);
      loadUsers();
      toast.success('Usuario eliminado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar usuario');
    }
    setLoading(false);
  };

  const changeUserPassword = async (userId, newPassword) => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    try {
      setLoading(true);
      await axios.put(`${API}/admin/users/${userId}/password`, {
        new_password: newPassword
      });
      setShowPasswordDialog(null);
      toast.success('Contraseña actualizada exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar contraseña');
    }
    setLoading(false);
  };

  const PasswordChangeDialog = ({ userId, username, onClose }) => {
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (newPassword !== confirmPassword) {
        toast.error('Las contraseñas no coinciden');
        return;
      }
      changeUserPassword(userId, newPassword);
    };

    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cambiar Contraseña</DialogTitle>
            <DialogDescription>
              Cambiar contraseña para el usuario: {username}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">Nueva Contraseña</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Mínimo 6 caracteres"
                required
                minLength={6}
                data-testid="new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirmar Contraseña</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repetir nueva contraseña"
                required
                minLength={6}
                data-testid="confirm-password-input"
              />
            </div>
            <div className="flex space-x-2">
              <Button type="submit" disabled={loading} data-testid="save-password-button">
                {loading ? 'Guardando...' : 'Guardar Contraseña'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose} data-testid="cancel-password-button">
                Cancelar
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    );
  };

  // Holdings management functions
  const loadUserHoldings = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/users/${userId}/holdings`);
      setUserHoldings(response.data);
    } catch (error) {
      toast.error('Error al cargar tenencias del usuario');
      setUserHoldings([]);
    }
  };

  const showUserHoldings = async (user) => {
    setShowHoldingsDialog(user);
    await loadUserHoldings(user.id);
  };

  const closeHoldingsDialog = () => {
    setShowHoldingsDialog(null);
    setUserHoldings([]);
    setEditingHolding(null);
    setNewHoldingForUser({
      filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
      legal_representative: '', amount_held: '', address: '', phone: '', email: ''
    });
    setEditHoldingData({
      filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
      legal_representative: '', amount_held: '', address: '', phone: '', email: ''
    });
  };

  const createHoldingForUser = async (userId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/admin/users/${userId}/holdings`, {
        ...newHoldingForUser,
        amount_held: parseFloat(newHoldingForUser.amount_held)
      });
      setNewHoldingForUser({
        filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
        legal_representative: '', amount_held: '', address: '', phone: '', email: ''
      });
      await loadUserHoldings(userId);
      toast.success('Tenencia creada exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear tenencia');
    }
    setLoading(false);
  };

  const startEditHolding = (holding) => {
    setEditingHolding(holding.id);
    setEditHoldingData({
      filing_date: holding.filing_date || '',
      isin_or_latinex_code: holding.isin_or_latinex_code || '',
      holder_name: holding.holder_name || '',
      holder_id: holding.holder_id || '',
      legal_representative: holding.legal_representative || '',
      amount_held: holding.amount_held || '',
      address: holding.address || '',
      phone: holding.phone || '',
      email: holding.email || ''
    });
  };

  const cancelEditHolding = () => {
    setEditingHolding(null);
    setEditHoldingData({
      filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
      legal_representative: '', amount_held: '', address: '', phone: '', email: ''
    });
  };

  const saveEditHolding = async (holdingId) => {
    setLoading(true);
    try {
      await axios.put(`${API}/admin/holdings/${holdingId}`, {
        ...editHoldingData,
        amount_held: parseFloat(editHoldingData.amount_held)
      });
      setEditingHolding(null);
      setEditHoldingData({
        filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
        legal_representative: '', amount_held: '', address: '', phone: '', email: ''
      });
      await loadUserHoldings(showHoldingsDialog.id);
      toast.success('Tenencia actualizada exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar tenencia');
    }
    setLoading(false);
  };

  const deleteHolding = async (holdingId, holderName) => {
    const confirmed = window.confirm(
      `¿Está seguro que desea eliminar la tenencia?\n\nTenedor: "${holderName}"\n\nEsta acción no se puede deshacer.`
    );
    
    if (!confirmed) return;

    try {
      setLoading(true);
      await axios.delete(`${API}/admin/holdings/${holdingId}`);
      await loadUserHoldings(showHoldingsDialog.id);
      toast.success('Tenencia eliminada exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar tenencia');
    }
    setLoading(false);
  };

  const HoldingsManagementDialog = ({ user, holdings, onClose }) => {
    const searchSecurityForHolding = async (code, isNewHolding = true) => {
      if (!code) return;
      try {
        const response = await axios.get(`${API}/securities/search/${code}`);
        toast.success(`Valor encontrado: ${response.data.security_description}`);
      } catch (error) {
        if (error.response?.status === 404) {
          toast.warning('Valor no encontrado en la base de datos');
        }
      }
    };

    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Gestionar Tenencias - {user.username}</DialogTitle>
            <DialogDescription>
              {user.brokerage_name} • {holdings.length} tenencias registradas
            </DialogDescription>
          </DialogHeader>
          
          {/* New Holding Form */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Agregar Nueva Tenencia</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Fecha de Presentación</Label>
                  <Input
                    type="date"
                    value={newHoldingForUser.filing_date}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, filing_date: e.target.value })}
                    required
                    data-testid="new-holding-filing-date"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Código ISIN/Latinex</Label>
                  <Input
                    value={newHoldingForUser.isin_or_latinex_code}
                    onChange={(e) => {
                      setNewHoldingForUser({ ...newHoldingForUser, isin_or_latinex_code: e.target.value });
                      searchSecurityForHolding(e.target.value);
                    }}
                    placeholder="ej: US698299AK07 o RPME0937500429A"
                    required
                    data-testid="new-holding-isin"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Nombre del Tenedor</Label>
                  <Input
                    value={newHoldingForUser.holder_name}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, holder_name: e.target.value })}
                    required
                    data-testid="new-holding-holder-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>ID del Tenedor</Label>
                  <Input
                    value={newHoldingForUser.holder_id}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, holder_id: e.target.value })}
                    placeholder="Cédula o RUC"
                    required
                    data-testid="new-holding-holder-id"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Representante Legal (opcional)</Label>
                  <Input
                    value={newHoldingForUser.legal_representative}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, legal_representative: e.target.value })}
                    data-testid="new-holding-legal-rep"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cantidad Tenida</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newHoldingForUser.amount_held}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, amount_held: e.target.value })}
                    required
                    data-testid="new-holding-amount"
                  />
                </div>
                <div className="md:col-span-2 space-y-2">
                  <Label>Dirección</Label>
                  <Textarea
                    value={newHoldingForUser.address}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, address: e.target.value })}
                    required
                    data-testid="new-holding-address"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Teléfono</Label>
                  <Input
                    type="tel"
                    value={newHoldingForUser.phone}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, phone: e.target.value })}
                    required
                    data-testid="new-holding-phone"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={newHoldingForUser.email}
                    onChange={(e) => setNewHoldingForUser({ ...newHoldingForUser, email: e.target.value })}
                    required
                    data-testid="new-holding-email"
                  />
                </div>
                <div className="md:col-span-2">
                  <Button 
                    onClick={() => createHoldingForUser(user.id)}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700"
                    data-testid="create-holding-for-user-button"
                  >
                    {loading ? 'Creando...' : 'Crear Tenencia'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Holdings Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Tenencias Existentes</CardTitle>
            </CardHeader>
            <CardContent>
              {holdings.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Código</TableHead>
                      <TableHead>Tenedor</TableHead>
                      <TableHead>Cantidad</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead className="w-32">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {holdings.map((holding) => (
                      <TableRow key={holding.id}>
                        {editingHolding === holding.id ? (
                          // Edit mode
                          <>
                            <TableCell>
                              <Input
                                type="date"
                                value={editHoldingData.filing_date}
                                onChange={(e) => setEditHoldingData({ ...editHoldingData, filing_date: e.target.value })}
                                className="w-full"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editHoldingData.isin_or_latinex_code}
                                onChange={(e) => setEditHoldingData({ ...editHoldingData, isin_or_latinex_code: e.target.value })}
                                className="w-full"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editHoldingData.holder_name}
                                onChange={(e) => setEditHoldingData({ ...editHoldingData, holder_name: e.target.value })}
                                className="w-full"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                step="0.01"
                                value={editHoldingData.amount_held}
                                onChange={(e) => setEditHoldingData({ ...editHoldingData, amount_held: e.target.value })}
                                className="w-full"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="email"
                                value={editHoldingData.email}
                                onChange={(e) => setEditHoldingData({ ...editHoldingData, email: e.target.value })}
                                className="w-full"
                              />
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-1">
                                <Button
                                  size="sm"
                                  onClick={() => saveEditHolding(holding.id)}
                                  disabled={loading}
                                  className="bg-green-600 hover:bg-green-700"
                                >
                                  ✓
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={cancelEditHolding}
                                  disabled={loading}
                                >
                                  ✗
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        ) : (
                          // View mode
                          <>
                            <TableCell className="text-sm">{holding.filing_date}</TableCell>
                            <TableCell className="font-mono text-sm">{holding.isin_or_latinex_code}</TableCell>
                            <TableCell>{holding.holder_name}</TableCell>
                            <TableCell className="text-right font-semibold">{holding.amount_held?.toLocaleString()}</TableCell>
                            <TableCell className="text-sm">{holding.email}</TableCell>
                            <TableCell>
                              <div className="flex space-x-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => startEditHolding(holding)}
                                  disabled={loading || editingHolding !== null}
                                >
                                  ✏️
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteHolding(holding.id, holding.holder_name)}
                                  disabled={loading || editingHolding !== null}
                                >
                                  🗑️
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No hay tenencias registradas para este usuario</p>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end space-x-2 mt-6">
            <Button variant="outline" onClick={onClose}>
              Cerrar
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">🏛️</span>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">Panel de Administración</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <input
                  id="excel-import"
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      // Validate file type
                      if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
                        toast.error('Formato de archivo no válido. Solo se permiten archivos Excel (.xlsx, .xls)');
                        e.target.value = '';
                        return;
                      }
                      // Validate file size (max 10MB)
                      if (file.size > 10 * 1024 * 1024) {
                        toast.error('El archivo es demasiado grande. Máximo 10MB permitido.');
                        e.target.value = '';
                        return;
                      }
                      setImportFile(file);
                      toast.info(`Archivo seleccionado: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
                    }
                  }}
                  className="hidden"
                />
                <Button
                  onClick={() => document.getElementById('excel-import').click()}
                  variant="outline"
                  className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                  data-testid="select-import-file-button"
                >
                  {importFile ? `Archivo: ${importFile.name}` : 'Seleccionar Archivo Excel'}
                </Button>
                {importFile && (
                  <Button
                    onClick={importFromExcel}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700"
                    data-testid="import-excel-button"
                  >
                    {loading ? 'Importando...' : `Importar ${importFile.name}`}
                  </Button>
                )}
              </div>
              <Button 
                onClick={exportToExcel}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
                data-testid="export-excel-button"
              >
                {loading ? 'Exportando...' : 'Exportar a Excel'}
              </Button>
              <Button 
                variant="outline" 
                onClick={logout}
                data-testid="admin-logout-button"
              >
                Cerrar Sesión
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="users" data-testid="users-tab">Usuarios</TabsTrigger>
            <TabsTrigger value="securities" data-testid="securities-tab">Valores ISIN</TabsTrigger>
            <TabsTrigger value="holdings" data-testid="holdings-tab">Tenencias</TabsTrigger>
            <TabsTrigger value="admins" data-testid="admins-tab">Administradores</TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Crear Nuevo Usuario</CardTitle>
                <CardDescription>Agregue un nuevo usuario del sistema de corretaje</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={createUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Usuario</Label>
                    <Input
                      id="username"
                      value={newUser.username}
                      onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                      required
                      data-testid="new-user-username"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Contraseña</Label>
                    <Input
                      id="password"
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      required
                      data-testid="new-user-password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      required
                      data-testid="new-user-email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="brokerage">Casa de Corretaje</Label>
                    <Input
                      id="brokerage"
                      value={newUser.brokerage_name}
                      onChange={(e) => setNewUser({ ...newUser, brokerage_name: e.target.value })}
                      required
                      data-testid="new-user-brokerage"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-4">
                    <Alert className="bg-blue-50 border-blue-200">
                      <AlertDescription>
                        💡 <strong>Gestión Completa de Usuarios y Tenencias:</strong> Como administrador, puede crear usuarios, 
                        editar sus datos (✏️), cambiar contraseñas (🔑), gestionar sus tenencias (📋), 
                        activar/desactivar (⏸️/▶️) y eliminar usuarios (🗑️).
                      </AlertDescription>
                    </Alert>
                    <Button type="submit" disabled={loading} data-testid="create-user-button">
                      {loading ? 'Creando...' : 'Crear Usuario'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Usuarios Registrados</CardTitle>
                <CardDescription>{users.length} usuarios registrados</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Casa de Corretaje</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Tenencias</TableHead>
                      <TableHead className="w-48">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        {editingUser === user.id ? (
                          // Edit mode
                          <>
                            <TableCell>
                              <Input
                                value={editUserData.username}
                                onChange={(e) => setEditUserData({ ...editUserData, username: e.target.value })}
                                placeholder="Nombre de usuario"
                                required
                                data-testid={`edit-username-${user.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="email"
                                value={editUserData.email}
                                onChange={(e) => setEditUserData({ ...editUserData, email: e.target.value })}
                                placeholder="Email"
                                required
                                data-testid={`edit-email-${user.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editUserData.brokerage_name}
                                onChange={(e) => setEditUserData({ ...editUserData, brokerage_name: e.target.value })}
                                placeholder="Casa de Corretaje"
                                required
                                data-testid={`edit-brokerage-${user.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <select
                                value={editUserData.is_active}
                                onChange={(e) => setEditUserData({ ...editUserData, is_active: e.target.value === 'true' })}
                                className="w-full p-2 border rounded"
                                data-testid={`edit-status-${user.id}`}
                              >
                                <option value={true}>Activo</option>
                                <option value={false}>Inactivo</option>
                              </select>
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => showUserHoldings(user)}
                                disabled={loading}
                                className="bg-blue-50 hover:bg-blue-100 border-blue-200 text-xs"
                                data-testid={`view-holdings-edit-${user.id}`}
                              >
                                {user.holdingsCount || 0} tenencias
                              </Button>
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-1">
                                <Button
                                  size="sm"
                                  onClick={() => saveEditUser(user.id)}
                                  disabled={loading}
                                  className="bg-green-600 hover:bg-green-700"
                                  data-testid={`save-user-${user.id}`}
                                >
                                  ✓
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={cancelEditUser}
                                  disabled={loading}
                                  data-testid={`cancel-edit-user-${user.id}`}
                                >
                                  ✗
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        ) : (
                          // View mode
                          <>
                            <TableCell className="font-medium">{user.username}</TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>{user.brokerage_name}</TableCell>
                            <TableCell>
                              <Badge variant={user.is_active ? "default" : "secondary"}>
                                {user.is_active ? 'Activo' : 'Inactivo'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => showUserHoldings(user)}
                                disabled={loading || editingUser !== null}
                                className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                                data-testid={`view-holdings-${user.id}`}
                              >
                                {user.holdingsCount || 0} tenencias
                              </Button>
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => startEditUser(user)}
                                  disabled={loading || editingUser !== null}
                                  data-testid={`edit-user-${user.id}`}
                                  title="Editar usuario"
                                >
                                  ✏️
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setShowPasswordDialog({ userId: user.id, username: user.username })}
                                  disabled={loading || editingUser !== null}
                                  className="bg-blue-50 hover:bg-blue-100"
                                  data-testid={`change-password-${user.id}`}
                                  title="Cambiar contraseña"
                                >
                                  🔑
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => showUserHoldings(user)}
                                  disabled={loading || editingUser !== null}
                                  className="bg-purple-50 hover:bg-purple-100"
                                  data-testid={`manage-holdings-${user.id}`}
                                  title="Gestionar tenencias"
                                >
                                  📋
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={() => toggleUserStatus(user.id)}
                                  disabled={loading || editingUser !== null}
                                  className={user.is_active ? "bg-yellow-50 hover:bg-yellow-100" : "bg-green-50 hover:bg-green-100"}
                                  data-testid={`toggle-user-${user.id}`}
                                  title={user.is_active ? "Desactivar usuario" : "Activar usuario"}
                                >
                                  {user.is_active ? '⏸️' : '▶️'}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteUser(user.id, user.username)}
                                  disabled={loading || editingUser !== null}
                                  data-testid={`delete-user-${user.id}`}
                                  title="Eliminar usuario"
                                >
                                  🗑️
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                {/* Password Change Dialog */}
                {showPasswordDialog && (
                  <PasswordChangeDialog
                    userId={showPasswordDialog.userId}
                    username={showPasswordDialog.username}
                    onClose={() => setShowPasswordDialog(null)}
                  />
                )}
                
                {/* Holdings Management Dialog */}
                {showHoldingsDialog && (
                  <HoldingsManagementDialog
                    user={showHoldingsDialog}
                    holdings={userHoldings}
                    onClose={closeHoldingsDialog}
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Securities Tab */}
          <TabsContent value="securities" className="space-y-6">
            <Alert className="bg-blue-50 border-blue-200">
              <AlertDescription>
                <strong>💡 Importación de Excel:</strong> Puede importar múltiples valores desde un archivo Excel. 
                El archivo debe contener las columnas: Código ISIN, Código Latinex, Descripción del Valor, Cupón, 
                Fecha de Emisión, Fecha de Vencimiento. Use el botón "Exportar a Excel" para ver el formato exacto.
              </AlertDescription>
            </Alert>
            
            <Card>
              <CardHeader>
                <CardTitle>Agregar Nuevo Valor</CardTitle>
                <CardDescription>Registre un nuevo bono con códigos ISIN y/o Latinex</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={createSecurity} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="isin">Código ISIN</Label>
                    <Input
                      id="isin"
                      placeholder="ej: US698299AK07"
                      value={newSecurity.isin_code}
                      onChange={(e) => setNewSecurity({ ...newSecurity, isin_code: e.target.value })}
                      data-testid="new-security-isin"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="latinex">Código Latinex</Label>
                    <Input
                      id="latinex"
                      placeholder="ej: RPME0937500429A"
                      value={newSecurity.latinex_code}
                      onChange={(e) => setNewSecurity({ ...newSecurity, latinex_code: e.target.value })}
                      data-testid="new-security-latinex"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <Label htmlFor="description">Descripción del Valor</Label>
                    <Input
                      id="description"
                      placeholder="ej: República de Panamá"
                      value={newSecurity.security_description}
                      onChange={(e) => setNewSecurity({ ...newSecurity, security_description: e.target.value })}
                      required
                      data-testid="new-security-description"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="coupon">Cupón</Label>
                    <Input
                      id="coupon"
                      placeholder="ej: 9.375%"
                      value={newSecurity.coupon}
                      onChange={(e) => setNewSecurity({ ...newSecurity, coupon: e.target.value })}
                      required
                      data-testid="new-security-coupon"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="issue_date">Fecha de Emisión</Label>
                    <Input
                      id="issue_date"
                      type="date"
                      value={newSecurity.issue_date}
                      onChange={(e) => setNewSecurity({ ...newSecurity, issue_date: e.target.value })}
                      required
                      data-testid="new-security-issue-date"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maturity_date">Fecha de Vencimiento</Label>
                    <Input
                      id="maturity_date"
                      type="date"
                      value={newSecurity.maturity_date}
                      onChange={(e) => setNewSecurity({ ...newSecurity, maturity_date: e.target.value })}
                      required
                      data-testid="new-security-maturity-date"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Button type="submit" disabled={loading} data-testid="create-security-button">
                      {loading ? 'Creando...' : 'Crear Valor'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Valores Registrados</CardTitle>
                    <CardDescription>{securities.length} valores en la base de datos</CardDescription>
                  </div>
                  {securities.length > 0 && (
                    <Button
                      onClick={clearAllSecurities}
                      disabled={loading}
                      variant="destructive"
                      className="bg-red-600 hover:bg-red-700"
                      data-testid="clear-all-securities-button"
                    >
                      {loading ? 'Limpiando...' : 'Limpiar Todos'}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ISIN</TableHead>
                      <TableHead>Latinex</TableHead>
                      <TableHead>Descripción</TableHead>
                      <TableHead>Cupón</TableHead>
                      <TableHead>Emisión</TableHead>
                      <TableHead>Vencimiento</TableHead>
                      <TableHead className="w-32">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {securities.map((security) => (
                      <TableRow key={security.id}>
                        {editingSecurity === security.id ? (
                          // Edit mode
                          <>
                            <TableCell>
                              <Input
                                value={editSecurityData.isin_code}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, isin_code: e.target.value })}
                                placeholder="Código ISIN"
                                className="font-mono text-sm"
                                data-testid={`edit-isin-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editSecurityData.latinex_code}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, latinex_code: e.target.value })}
                                placeholder="Código Latinex"
                                className="font-mono text-sm"
                                data-testid={`edit-latinex-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editSecurityData.security_description}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, security_description: e.target.value })}
                                placeholder="Descripción del valor"
                                required
                                data-testid={`edit-description-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                value={editSecurityData.coupon}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, coupon: e.target.value })}
                                placeholder="Cupón"
                                required
                                data-testid={`edit-coupon-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="date"
                                value={editSecurityData.issue_date}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, issue_date: e.target.value })}
                                required
                                data-testid={`edit-issue-date-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="date"
                                value={editSecurityData.maturity_date}
                                onChange={(e) => setEditSecurityData({ ...editSecurityData, maturity_date: e.target.value })}
                                required
                                data-testid={`edit-maturity-date-${security.id}`}
                              />
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-1">
                                <Button
                                  size="sm"
                                  onClick={() => saveEditSecurity(security.id)}
                                  disabled={loading}
                                  className="bg-green-600 hover:bg-green-700"
                                  data-testid={`save-security-${security.id}`}
                                >
                                  ✓
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={cancelEditSecurity}
                                  disabled={loading}
                                  data-testid={`cancel-edit-${security.id}`}
                                >
                                  ✗
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        ) : (
                          // View mode
                          <>
                            <TableCell className="font-mono text-sm">{security.isin_code || '-'}</TableCell>
                            <TableCell className="font-mono text-sm">{security.latinex_code || '-'}</TableCell>
                            <TableCell className="max-w-xs truncate" title={security.security_description}>
                              {security.security_description}
                            </TableCell>
                            <TableCell className="font-semibold">{security.coupon}</TableCell>
                            <TableCell className="text-sm">{security.issue_date}</TableCell>
                            <TableCell className="text-sm">{security.maturity_date}</TableCell>
                            <TableCell>
                              <div className="flex space-x-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => startEditSecurity(security)}
                                  disabled={loading || editingSecurity !== null}
                                  data-testid={`edit-security-${security.id}`}
                                >
                                  ✏️
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteSecurity(security.id, security.security_description)}
                                  disabled={loading || editingSecurity !== null}
                                  data-testid={`delete-security-${security.id}`}
                                >
                                  🗑️
                                </Button>
                              </div>
                            </TableCell>
                          </>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Holdings Tab */}
          <TabsContent value="holdings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Todas las Tenencias</CardTitle>
                <CardDescription>Vista consolidada de todas las tenencias registradas</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Código</TableHead>
                      <TableHead>Tenedor</TableHead>
                      <TableHead>Cantidad</TableHead>
                      <TableHead>Email</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {holdings.map((holding) => (
                      <TableRow key={holding.id}>
                        <TableCell>{holding.filing_date}</TableCell>
                        <TableCell className="font-mono text-sm">{holding.isin_or_latinex_code}</TableCell>
                        <TableCell>{holding.holder_name}</TableCell>
                        <TableCell className="text-right font-semibold">{holding.amount_held.toLocaleString()}</TableCell>
                        <TableCell>{holding.email}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Admins Tab */}
          <TabsContent value="admins" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Crear Nuevo Administrador</CardTitle>
                <CardDescription>Agregue un nuevo administrador del sistema</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={createAdmin} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="admin-username">Usuario</Label>
                    <Input
                      id="admin-username"
                      value={newAdmin.username}
                      onChange={(e) => setNewAdmin({ ...newAdmin, username: e.target.value })}
                      required
                      data-testid="new-admin-username"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="admin-email">Email</Label>
                    <Input
                      id="admin-email"
                      type="email"
                      value={newAdmin.email}
                      onChange={(e) => setNewAdmin({ ...newAdmin, email: e.target.value })}
                      required
                      data-testid="new-admin-email"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <Label htmlFor="admin-password">Contraseña</Label>
                    <Input
                      id="admin-password"
                      type="password"
                      value={newAdmin.password}
                      onChange={(e) => setNewAdmin({ ...newAdmin, password: e.target.value })}
                      required
                      data-testid="new-admin-password"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Button type="submit" disabled={loading} data-testid="create-admin-button">
                      {loading ? 'Creando...' : 'Crear Administrador'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Administradores Registrados</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Usuario</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Fecha de Creación</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {admins.map((admin) => (
                      <TableRow key={admin.id}>
                        <TableCell className="font-medium">{admin.username}</TableCell>
                        <TableCell>{admin.email}</TableCell>
                        <TableCell>{new Date(admin.created_at).toLocaleDateString('es-ES')}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// User Dashboard
function UserDashboard() {
  const [holdings, setHoldings] = useState([]);
  const [newHolding, setNewHolding] = useState({
    filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
    legal_representative: '', amount_held: '', address: '', phone: '', email: ''
  });
  const [securityInfo, setSecurityInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    loadHoldings();
  }, []);

  const loadHoldings = async () => {
    try {
      const response = await axios.get(`${API}/holdings`);
      setHoldings(response.data);
    } catch (error) {
      toast.error('Error al cargar tenencias');
    }
  };

  const searchSecurity = async (code) => {
    if (!code) {
      setSecurityInfo(null);
      return;
    }
    try {
      const response = await axios.get(`${API}/securities/search/${code}`);
      setSecurityInfo(response.data);
      toast.success('Valor encontrado');
    } catch (error) {
      setSecurityInfo(null);
      if (error.response?.status === 404) {
        toast.warning('Valor no encontrado en la base de datos');
      }
    }
  };

  const createHolding = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/holdings`, {
        ...newHolding,
        amount_held: parseFloat(newHolding.amount_held)
      });
      setNewHolding({
        filing_date: '', isin_or_latinex_code: '', holder_name: '', holder_id: '',
        legal_representative: '', amount_held: '', address: '', phone: '', email: ''
      });
      setSecurityInfo(null);
      loadHoldings();
      toast.success('Tenencia registrada exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrar tenencia');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">🏛️</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Panel de Usuario</h1>
                <p className="text-sm text-gray-600">{user?.brokerage_name}</p>
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={logout}
              data-testid="user-logout-button"
            >
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* New Holding Form */}
          <Card>
            <CardHeader>
              <CardTitle>Registrar Nueva Tenencia</CardTitle>
              <CardDescription>Complete la información del tenedor de bonos</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={createHolding} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="filing_date">Fecha de Presentación</Label>
                    <Input
                      id="filing_date"
                      type="date"
                      value={newHolding.filing_date}
                      onChange={(e) => setNewHolding({ ...newHolding, filing_date: e.target.value })}
                      required
                      data-testid="filing-date-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="code">Código ISIN/Latinex</Label>
                    <Input
                      id="code"
                      placeholder="ej: US698299AK07 o RPME0937500429A"
                      value={newHolding.isin_or_latinex_code}
                      onChange={(e) => {
                        setNewHolding({ ...newHolding, isin_or_latinex_code: e.target.value });
                        searchSecurity(e.target.value);
                      }}
                      required
                      data-testid="isin-code-input"
                    />
                  </div>
                </div>

                {securityInfo && (
                  <Alert className="bg-green-50 border-green-200">
                    <AlertDescription>
                      <strong>Valor encontrado:</strong> {securityInfo.security_description} - 
                      Cupón: {securityInfo.coupon} - Vence: {securityInfo.maturity_date}
                    </AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="holder_name">Nombre del Tenedor</Label>
                    <Input
                      id="holder_name"
                      value={newHolding.holder_name}
                      onChange={(e) => setNewHolding({ ...newHolding, holder_name: e.target.value })}
                      required
                      data-testid="holder-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="holder_id">ID del Tenedor</Label>
                    <Input
                      id="holder_id"
                      placeholder="Cédula o RUC"
                      value={newHolding.holder_id}
                      onChange={(e) => setNewHolding({ ...newHolding, holder_id: e.target.value })}
                      required
                      data-testid="holder-id-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="legal_rep">Representante Legal (opcional)</Label>
                  <Input
                    id="legal_rep"
                    value={newHolding.legal_representative}
                    onChange={(e) => setNewHolding({ ...newHolding, legal_representative: e.target.value })}
                    data-testid="legal-rep-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="amount">Cantidad Tenida</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={newHolding.amount_held}
                    onChange={(e) => setNewHolding({ ...newHolding, amount_held: e.target.value })}
                    required
                    data-testid="amount-held-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Dirección</Label>
                  <Textarea
                    id="address"
                    value={newHolding.address}
                    onChange={(e) => setNewHolding({ ...newHolding, address: e.target.value })}
                    required
                    data-testid="address-input"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Teléfono</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={newHolding.phone}
                      onChange={(e) => setNewHolding({ ...newHolding, phone: e.target.value })}
                      required
                      data-testid="phone-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={newHolding.email}
                      onChange={(e) => setNewHolding({ ...newHolding, email: e.target.value })}
                      required
                      data-testid="email-input"
                    />
                  </div>
                </div>

                <Button 
                  type="submit" 
                  disabled={loading} 
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                  data-testid="create-holding-button"
                >
                  {loading ? 'Registrando...' : 'Registrar Tenencia'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Holdings List */}
          <Card>
            <CardHeader>
              <CardTitle>Mis Tenencias Registradas</CardTitle>
              <CardDescription>{holdings.length} tenencias registradas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {holdings.map((holding) => (
                  <div key={holding.id} className="border rounded-lg p-4 space-y-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold">{holding.holder_name}</p>
                        <p className="text-sm text-gray-600">{holding.holder_id}</p>
                      </div>
                      <Badge variant="outline">{holding.filing_date}</Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-medium">Código:</span> {holding.isin_or_latinex_code}
                      </div>
                      <div>
                        <span className="font-medium">Cantidad:</span> {holding.amount_held.toLocaleString()}
                      </div>
                    </div>
                    {holding.security_info && (
                      <p className="text-xs text-gray-500">
                        {holding.security_info.security_description} - {holding.security_info.coupon}
                      </p>
                    )}
                  </div>
                ))}
                {holdings.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <p>No hay tenencias registradas aún</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  if (user.user_type === 'admin') {
    return <AdminDashboard />;
  }

  return <UserDashboard />;
}

function AppWithProviders() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <App />
        <Toaster richColors position="top-right" />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default AppWithProviders;
