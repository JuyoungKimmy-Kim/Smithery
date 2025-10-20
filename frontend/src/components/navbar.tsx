import React from "react";
import Link from "next/link";
import {
  RectangleStackIcon,
  UserCircleIcon,
  CommandLineIcon,
  XMarkIcon,
  Bars3Icon,
  ChevronDownIcon,
  LanguageIcon,
  BookOpenIcon,
} from "@heroicons/react/24/solid";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

export function Navbar() {
  const [open, setOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const [wikiMenuOpen, setWikiMenuOpen] = React.useState(false);
  const [showSignInModal, setShowSignInModal] = React.useState(false);
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();

  const handleOpen = () => setOpen((cur) => !cur);
  const handleUserMenuToggle = () => setUserMenuOpen((cur) => !cur);
  const handleWikiMenuToggle = () => setWikiMenuOpen((cur) => !cur);
  
  const handleRegisterClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      setShowSignInModal(true);
      return;
    }
    router.push("/submit");
  };

  const handleLoginClick = () => {
    router.push('/login');
  };

  const handleLogoutClick = () => {
    logout();
    setUserMenuOpen(false);
    router.push('/');
    // 페이지 새로고침
    window.location.reload();
  };

  const handleMyPageClick = () => {
    router.push('/mypage');
    setUserMenuOpen(false);
  };

  const handleSignInModalClose = () => {
    setShowSignInModal(false);
  };

  const handleSignInModalConfirm = () => {
    setShowSignInModal(false);
    router.push('/login');
  };

  const handleLanguageToggle = () => {
    setLanguage(language === 'ko' ? 'en' : 'ko');
  };

  const handleWikiLinkClick = () => {
    setWikiMenuOpen(false);
    setOpen(false);
  };

  React.useEffect(() => {
    window.addEventListener(
      "resize",
      () => window.innerWidth >= 960 && setOpen(false)
    );
  }, []);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuOpen && !(event.target as Element).closest('.user-menu')) {
        setUserMenuOpen(false);
      }
      if (wikiMenuOpen && !(event.target as Element).closest('.wiki-menu')) {
        setWikiMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [userMenuOpen, wikiMenuOpen]);

  return (
    <>
      <nav className="sticky top-0 z-50 bg-blue-50 shadow-lg">
        <div className="container mx-auto flex items-center justify-between px-4 py-3">
          <Link
            href="/"
            className="text-lg font-bold text-blue-gray-900 nav-link"
            data-nav-link="true"
          >
            MCP Server Hub
          </Link>

          <div className="hidden items-center gap-4 lg:flex">
            {/* Wiki Dropdown */}
            <div className="relative wiki-menu">
              <button
                onClick={handleWikiMenuToggle}
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-gray-900 transition-colors rounded-lg hover:bg-gray-100"
              >
                <BookOpenIcon className="h-5 w-5" />
                <span className="text-sm font-medium">{t('nav.wiki')}</span>
                <ChevronDownIcon className="h-4 w-4" />
              </button>
              
              {wikiMenuOpen && (
                <div className="absolute left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                  <Link
                    href="/wiki/getting-started"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    {t('nav.gettingStarted')}
                  </Link>
                  <Link
                    href="/wiki/how-to-use"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    {t('nav.howToUse')}
                  </Link>
                  <Link
                    href="/wiki/roadmap"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    {t('nav.roadmap')}
                  </Link>
                </div>
              )}
            </div>
            
            <button
              onClick={handleLanguageToggle}
              className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-gray-900 transition-colors rounded-lg hover:bg-gray-100"
              title={language === 'ko' ? '한국어' : 'English'}
            >
              <LanguageIcon className="h-5 w-5" />
              <span className="text-sm font-medium">{language === 'ko' ? 'KO' : 'EN'}</span>
            </button>
            
            {isAuthenticated ? (
              <div className="relative user-menu">
                <button
                  onClick={handleUserMenuToggle}
                  className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-gray-900 transition-colors rounded-lg hover:bg-gray-100"
                >
                  <UserCircleIcon className="h-5 w-5" />
                  <span className="text-sm font-medium">{user?.username}</span>
                  <ChevronDownIcon className="h-4 w-4" />
                </button>
                
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                    <button
                      onClick={handleMyPageClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2"
                    >
                      <UserCircleIcon className="h-4 w-4" />
                      {t('nav.mypage')}
                    </button>
                    <hr className="my-1" />
                    <button
                      onClick={handleLogoutClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      {t('nav.signout')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                onClick={handleLoginClick}
                className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              >
                {t('nav.signin')}
              </button>
            )}

            <button 
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={handleRegisterClick}
            >
              {t('nav.register')}
            </button>
          </div>
          <button
            onClick={handleOpen}
            className="ml-auto inline-block lg:hidden p-2 text-gray-700 hover:text-gray-900"
          >
            {open ? (
              <XMarkIcon className="h-6 w-6" />
            ) : (
              <Bars3Icon className="h-6 w-6" />
            )}
          </button>
        </div>
        {open && (
          <div className="lg:hidden bg-blue-50">
            <div className="container mx-auto px-4 py-4">
              <div className="mt-4 space-y-2">
                {/* Wiki Section - Mobile */}
                <div className="border-b border-gray-300 pb-2 mb-2">
                  <div className="flex items-center gap-2 px-4 py-2 text-gray-900 font-medium">
                    <BookOpenIcon className="h-5 w-5" />
                    {t('nav.wiki')}
                  </div>
                  <Link
                    href="/wiki/getting-started"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-8 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    {t('nav.gettingStarted')}
                  </Link>
                  <Link
                    href="/wiki/how-to-use"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-8 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    {t('nav.howToUse')}
                  </Link>
                  <Link
                    href="/wiki/roadmap"
                    onClick={handleWikiLinkClick}
                    className="block w-full px-8 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    {t('nav.roadmap')}
                  </Link>
                </div>
                
                <button
                  onClick={handleLanguageToggle}
                  className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors flex items-center gap-2"
                >
                  <LanguageIcon className="h-5 w-5" />
                  {language === 'ko' ? '한국어 (KO)' : 'English (EN)'}
                </button>
                
                {isAuthenticated ? (
                  <>
                    <button
                      onClick={handleMyPageClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors flex items-center gap-2"
                    >
                      <UserCircleIcon className="h-4 w-4" />
                      {t('nav.mypage')}
                    </button>
                    <button 
                      onClick={handleLogoutClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      {t('nav.signout')}
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={handleLoginClick}
                    className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    {t('nav.signin')}
                  </button>
                )}

                <button 
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={handleRegisterClick}
                >
                  {t('nav.register')}
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Sign In Required Modal */}
      {showSignInModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                {t('nav.signInRequired')}
              </h3>
              <p className="text-gray-600 text-center mb-6">
                {t('nav.signInRequiredDesc')}
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleSignInModalClose}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  {t('nav.cancel')}
                </button>
                <button
                  onClick={handleSignInModalConfirm}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
                >
                  {t('nav.signin')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Navbar;
