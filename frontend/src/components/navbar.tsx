import React from "react";
import {
  RectangleStackIcon,
  UserCircleIcon,
  CommandLineIcon,
  XMarkIcon,
  Bars3Icon,
  ChevronDownIcon,
} from "@heroicons/react/24/solid";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export function Navbar() {
  const [open, setOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();

  const handleOpen = () => setOpen((cur) => !cur);
  const handleUserMenuToggle = () => setUserMenuOpen((cur) => !cur);
  
  const handleDeployClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      alert('Sign in required.');
      router.push('/login');
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
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [userMenuOpen]);

  return (
    <>
      <nav className="sticky top-0 z-50 bg-blue-50 shadow-lg">
        <div className="container mx-auto flex items-center justify-between px-4 py-3">
          <a
            href="/"
            className="text-lg font-bold text-blue-gray-900"
          >
            MCP Server Hub
          </a>

          <div className="hidden items-center gap-4 lg:flex">
            <button 
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={handleDeployClick}
            >
              Deploy Server
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
                      My Page
                    </button>
                    <hr className="my-1" />
                    <button
                      onClick={handleLogoutClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                onClick={handleLoginClick}
                className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              >
                Sign In
              </button>
            )}
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
                <button 
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={handleDeployClick}
                >
                  Deploy Server
                </button>
                
                {isAuthenticated ? (
                  <>
                    <button
                      onClick={handleMyPageClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors flex items-center gap-2"
                    >
                      <UserCircleIcon className="h-4 w-4" />
                      My Page
                    </button>
                    <button 
                      onClick={handleLogoutClick}
                      className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      Sign Out
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={handleLoginClick}
                    className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    Sign In
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}

export default Navbar;
