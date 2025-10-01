const CURRENT_YEAR = new Date().getFullYear();
const LINKS = ["Company", "About Us", "Team", "Products", "Blog"];

export function Footer() {
  return (
    <footer className="pb-5 p-10 md:pt-10 bg-gradient-to-b from-gray-100 to-gray-200 border-t border-gray-300 mt-16">
      <div className="container flex flex-col mx-auto">
        <div className="flex flex-col md:flex-row items-center !justify-between">
          <a
            href="https://www.material-tailwind.com"
            target="_blank"
            className="text-xl font-semibold text-gray-900"
          >
           AI Agent Group
          </a>
          <ul className="flex justify-center my-4 md:my-0 w-max mx-auto items-center gap-4">
            {LINKS.map((link, index) => (
              <li key={index}>
                <a
                  href="#"
                  className="font-normal text-gray-700 hover:text-gray-900 transition-colors"
                >
                  {link}
                </a>
              </li>
            ))}
          </ul>
          <div className="flex w-fit justify-center gap-2">
            <button className="p-2 text-gray-700 hover:text-gray-900 transition-colors">
              <i className="fa-brands fa-twitter text-lg" />
            </button>
            <button className="p-2 text-gray-700 hover:text-gray-900 transition-colors">
              <i className="fa-brands fa-youtube text-lg" />
            </button>
            <button className="p-2 text-gray-700 hover:text-gray-900 transition-colors">
              <i className="fa-brands fa-instagram text-lg" />
            </button>
            <button className="p-2 text-gray-700 hover:text-gray-900 transition-colors">
              <i className="fa-brands fa-github text-lg" />
            </button>
          </div>
        </div>
        <p className="text-center mt-12 font-normal text-gray-700">
          &copy; {CURRENT_YEAR} Made with{" "}
          <a href="https://www.material-tailwind.com" target="_blank" className="text-blue-600 hover:text-blue-800">
            AI Agent Group
          </a>{" "}
          by{" "}
          <a href="https://www.creative-tim.com" target="_blank" className="text-blue-600 hover:text-blue-800">
            Creative Juyoung Kim
          </a>
          .
        </p>
      </div>
    </footer>
  );
}

export default Footer;
