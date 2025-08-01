const CURRENT_YEAR = new Date().getFullYear();
const LINKS = ["Company", "About Us", "Team", "Products", "Blog"];

export function Footer() {
  return (
    <footer className="pb-5 p-10 md:pt-10">
      <div className="container flex flex-col mx-auto">
        <div className="flex !w-full py-10 mb-5 md:mb-20 flex-col justify-center !items-center bg-gray-900 container max-w-6xl mx-auto rounded-2xl p-5 ">
          <h2 className="text-2xl md:text-3xl text-center font-bold text-white">
            Join our community!
          </h2>
          <p className="md:w-7/12 text-center my-3 text-base text-white">
            Get news in your inbox every week! We hate spam too, so no worries
            about this.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 md:flex-row">
            <div className="w-80">
              <input 
                type="email" 
                placeholder="Email" 
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button className="px-6 py-2 bg-white text-gray-900 font-medium rounded-lg hover:bg-gray-100 transition-colors lg:w-32 w-full">
              subscribe
            </button>
          </div>
        </div>
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
