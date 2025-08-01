"use client";

import Image from "next/image";


function Hero() {
  return (
    <header className="mt-5 bg-black py-16">
      <div className="container mx-auto flex flex-col justify-center items-center min-h-[320px] text-center">
        <h1
          className="mx-auto w-full text-[30px] lg:text-[48px] font-bold leading-[45px] lg:leading-[60px] text-white"
        >
          DS Agent's Gateway
        </h1>
        <p
          className="mx-auto mt-8 mb-4 w-full px-8 text-gray-300 lg:w-10/12 lg:px-12 xl:w-8/12 xl:px-20 text-lg"
        >
          Integrate your AI with 5566 skills and extensions built by the community.
        </p>
        <div className="grid place-items-start justify-center gap-2">
          <div className="mt-8 flex flex-col items-center justify-center gap-4 md:flex-row">
            <div className="w-80">
              <input 
                type="text" 
                placeholder="find your mcp server" 
                className="w-full px-3 py-2 bg-gray-800 text-white border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
              />
            </div>
            <button className="px-6 py-2 bg-white text-black font-medium rounded-lg hover:bg-gray-100 transition-colors lg:w-max shrink-0 w-full">
              Search
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
export default Hero;
