import React from "react";
import {
  RectangleStackIcon,
  UserCircleIcon,
  CommandLineIcon,
  XMarkIcon,
  Bars3Icon,
} from "@heroicons/react/24/solid";
import { useRouter } from "next/navigation";

const NAV_MENU = [
  {
    name: "Page",
    icon: RectangleStackIcon,
  },
  {
    name: "Account",
    icon: UserCircleIcon,
  },
  {
    name: "Docs",
    icon: CommandLineIcon,
    href: "https://www.material-tailwind.com/docs/react/installation",
  },
];

interface NavItemProps {
  children: React.ReactNode;
  href?: string;
}

function NavItem({ children, href }: NavItemProps) {
  return (
    <li>
      <a
        href={href || "#"}
        target={href ? "_blank" : "_self"}
        className="flex items-center gap-2 font-medium text-gray-900"
      >
        {children}
      </a>
    </li>
  );
}

export function Navbar() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  const handleOpen = () => setOpen((cur) => !cur);
  const handleDeployClick = (e: React.MouseEvent) => {
    e.preventDefault();
    router.push("/submit");
  };

  React.useEffect(() => {
    window.addEventListener(
      "resize",
      () => window.innerWidth >= 960 && setOpen(false)
    );
  }, []);

  return (
    <nav className="border-0 sticky top-0 z-50 bg-white shadow-sm">
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        <a
          href="/"
          className="text-lg font-bold text-blue-gray-900"
        >
          MCP Server Hub
        </a>
        <ul className="ml-10 hidden items-center gap-8 lg:flex">
          {NAV_MENU.map(({ name, icon: Icon, href }) => (
            <NavItem key={name} href={href}>
              <Icon className="h-5 w-5" />
              {name}
            </NavItem>
          ))}
        </ul>
        <div className="hidden items-center gap-2 lg:flex">
          <button className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors">
            Sign In
          </button>
          <button 
            className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            onClick={handleDeployClick}
          >
            Deploy Server
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
        <div className="lg:hidden border-t border-gray-200 bg-white">
          <div className="container mx-auto px-4 py-4">
            <ul className="space-y-4">
              {NAV_MENU.map(({ name, icon: Icon, href }) => (
                <NavItem key={name} href={href}>
                  <Icon className="h-5 w-5" />
                  {name}
                </NavItem>
              ))}
            </ul>
            <div className="mt-4 space-y-2">
              <button className="w-full px-4 py-2 text-left text-gray-700 hover:text-gray-900 transition-colors">
                Sign In
              </button>
              <button 
                className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                onClick={handleDeployClick}
              >
                Deploy Server
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
