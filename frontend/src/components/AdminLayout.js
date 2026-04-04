import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Building2,
  Users,
  CreditCard,
  DollarSign,
  Key,
  FileText,
  BarChart3,
  ScrollText,
  LogOut,
  Menu,
  X,
  Home,
  Database,
  Search,
  Globe,
  ChevronDown,
  Wrench
} from 'lucide-react';

const AdminLayout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [seoOpen, setSeoOpen] = useState(location.pathname.startsWith('/admin/seo'));
  const [dbOpen, setDbOpen] = useState(location.pathname.startsWith('/admin/sync') || location.pathname.startsWith('/admin/db') || location.pathname.startsWith('/admin/caen'));

  const navigationItems = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Firme', path: '/admin/companies', icon: Building2 },
    { name: 'Utilizatori', path: '/admin/users', icon: Users },
    { name: 'Elasticsearch', path: '/admin/elasticsearch', icon: Search },
    { name: 'Abonamente', path: '/admin/subscriptions', icon: CreditCard },
    { name: 'Plăți', path: '/admin/payments', icon: DollarSign },
    { name: 'API Keys', path: '/admin/api-keys', icon: Key },
    { name: 'Analiză Financiară', path: '/admin/financial', icon: BarChart3 },
    { name: 'Audit Log', path: '/admin/audit', icon: ScrollText },
  ];

  const dbSubItems = [
    { name: 'Sincronizare', path: '/admin/sync' },
    { name: 'Optimizare DB', path: '/admin/db-optimize' },
    { name: 'Coduri CAEN', path: '/admin/caen' },
  ];

  const seoSubItems = [
    { name: 'SEO Templates', path: '/admin/seo' },
    { name: 'Generator Sitemap', path: '/admin/seo/sitemap' },
    { name: 'Generare Texte AI', path: '/admin/seo-gen' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Bar */}
      <div className="fixed top-0 left-0 right-0 h-14 bg-card border-b border-border z-50 flex items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
            data-testid="admin-sidebar-toggle"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <Link to="/" className="flex items-center space-x-2" data-testid="admin-home-link">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">m</span>
            </div>
            <span className="text-lg font-semibold hidden sm:inline">RapoarteFirme Admin</span>
          </Link>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/"
            className="flex items-center space-x-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            data-testid="admin-view-site"
          >
            <Home className="w-4 h-4" />
            <span className="hidden sm:inline">Vezi site</span>
          </Link>
          
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-secondary rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm font-medium">{user?.name || user?.email}</span>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-14 bottom-0 w-64 bg-card border-r border-border transition-transform duration-300 z-40 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
        data-testid="admin-sidebar"
      >
        <nav className="flex flex-col h-full p-4">
          <div className="flex-1 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || 
                               (item.path !== '/admin' && location.pathname.startsWith(item.path));
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`admin-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }`}
                  onClick={() => {
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}

            {/* DB submenu */}
            <div>
              <button
                onClick={() => setDbOpen(!dbOpen)}
                data-testid="admin-nav-baza-de-date"
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors ${
                  location.pathname.startsWith('/admin/sync') || location.pathname.startsWith('/admin/db') || location.pathname.startsWith('/admin/caen')
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Database className="w-5 h-5" />
                  <span className="font-medium">Baza de Date</span>
                </div>
                <ChevronDown className={`w-4 h-4 transition-transform ${dbOpen ? 'rotate-180' : ''}`} />
              </button>
              {dbOpen && (
                <div className="ml-4 mt-1 space-y-0.5">
                  {dbSubItems.map((sub) => (
                    <Link
                      key={sub.path}
                      to={sub.path}
                      data-testid={`admin-nav-${sub.name.toLowerCase().replace(/\s+/g, '-')}`}
                      className={`flex items-center px-3 py-2 rounded-lg text-sm transition-colors ${
                        location.pathname === sub.path
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      }`}
                      onClick={() => {
                        if (window.innerWidth < 1024) setSidebarOpen(false);
                      }}
                    >
                      {sub.name}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* SEO submenu */}
            <div>
              <button
                onClick={() => setSeoOpen(!seoOpen)}
                data-testid="admin-nav-seo"
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors ${
                  location.pathname.startsWith('/admin/seo')
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Globe className="w-5 h-5" />
                  <span className="font-medium">SEO</span>
                </div>
                <ChevronDown className={`w-4 h-4 transition-transform ${seoOpen ? 'rotate-180' : ''}`} />
              </button>
              {seoOpen && (
                <div className="ml-4 mt-1 space-y-0.5">
                  {seoSubItems.map((sub) => (
                    <Link
                      key={sub.path}
                      to={sub.path}
                      data-testid={`admin-nav-${sub.name.toLowerCase().replace(/\s+/g, '-')}`}
                      className={`flex items-center px-3 py-2 rounded-lg text-sm transition-colors ${
                        location.pathname === sub.path
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      }`}
                      onClick={() => {
                        if (window.innerWidth < 1024) setSidebarOpen(false);
                      }}
                    >
                      {sub.name}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors mt-4"
            data-testid="admin-logout"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Deconectare</span>
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main
        className={`pt-14 transition-all duration-300 ${
          sidebarOpen ? 'lg:pl-64' : 'pl-0'
        }`}
      >
        <div className="p-6">
          {children}
        </div>
      </main>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default AdminLayout;
