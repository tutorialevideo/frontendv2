import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { AuthProvider } from './contexts/AuthContext';
import { CreditsProvider } from './contexts/CreditsContext';
import Header from './components/Header';
import Footer from './components/Footer';
import NoCreditsModal from './components/NoCreditsModal';

const HomePage = lazy(() => import('./pages/HomePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const CompanyPage = lazy(() => import('./pages/CompanyPage'));
const JudeteListPage = lazy(() => import('./pages/JudeteListPage'));
const JudetPage = lazy(() => import('./pages/JudetPage'));
const LocalitatePage = lazy(() => import('./pages/LocalitatePage'));
const CaenListPage = lazy(() => import('./pages/CaenListPage'));
const CaenPage = lazy(() => import('./pages/CaenPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const AccountPage = lazy(() => import('./pages/AccountPage'));
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'));
const SubscriptionPage = lazy(() => import('./pages/SubscriptionPage'));
const CreditsPage = lazy(() => import('./pages/CreditsPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const AdminCompaniesPage = lazy(() => import('./pages/AdminCompaniesPage'));
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage'));
const AdminAuditPage = lazy(() => import('./pages/AdminAuditPage'));
const AdminSyncPage = lazy(() => import('./pages/AdminSyncPage'));
const ApiKeysPage = lazy(() => import('./pages/ApiKeysPage'));
const AdminApiKeysPage = lazy(() => import('./pages/AdminApiKeysPage'));
const AdminElasticsearchPage = lazy(() => import('./pages/AdminElasticsearchPage'));
const AdminSeoPage = lazy(() => import('./pages/AdminSeoPage'));
const AdminSitemapPage = lazy(() => import('./pages/AdminSitemapPage'));
const AdminFinancialDashboard = lazy(() => import('./pages/AdminFinancialDashboard'));

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
  </div>
);

function AppContent() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');

  return (
    <div className="min-h-screen flex flex-col">
      {!isAdminRoute && <Header />}
      <main className="flex-1">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/firma/:slug" element={<CompanyPage />} />
            <Route path="/judete" element={<JudeteListPage />} />
            <Route path="/judet/:judetSlug" element={<JudetPage />} />
            <Route path="/judet/:judetSlug/:localitateSlug" element={<LocalitatePage />} />
            <Route path="/caen" element={<CaenListPage />} />
            <Route path="/caen/:cod" element={<CaenPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/account/favorites" element={<FavoritesPage />} />
            <Route path="/account/subscription" element={<SubscriptionPage />} />
            <Route path="/account/credits" element={<CreditsPage />} />
            <Route path="/account/api-keys" element={<ApiKeysPage />} />
            
            {/* Admin Routes */}
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/companies" element={<AdminCompaniesPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
            <Route path="/admin/sync" element={<AdminSyncPage />} />
            <Route path="/admin/api-keys" element={<AdminApiKeysPage />} />
            <Route path="/admin/elasticsearch" element={<AdminElasticsearchPage />} />
            <Route path="/admin/seo" element={<AdminSeoPage />} />
            <Route path="/admin/seo/sitemap" element={<AdminSitemapPage />} />
            <Route path="/admin/financial" element={<AdminFinancialDashboard />} />
          </Routes>
        </Suspense>
      </main>
      {!isAdminRoute && <Footer />}
      <NoCreditsModal />
    </div>
  );
}

function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
        <CreditsProvider>
          <Router>
            <AppContent />
          </Router>
        </CreditsProvider>
      </AuthProvider>
    </HelmetProvider>
  );
}

export default App;