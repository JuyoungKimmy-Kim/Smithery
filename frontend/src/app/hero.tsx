"use client";

import Image from "next/image";
import { Button, Typography, Input } from "@material-tailwind/react";


function Hero() {
  return (
    <header className="mt-5 bg-black py-16">
      <div className="container mx-auto flex flex-col justify-center items-center min-h-[320px] text-center">
        <Typography
          color="white"
          className="mx-auto w-full text-[30px] lg:text-[48px] font-bold leading-[45px] lg:leading-[60px]"
        >
          DS Agent's Gateway
        </Typography>
        <Typography
          variant="lead"
          className="mx-auto mt-8 mb-4 w-full px-8 !text-gray-300 lg:w-10/12 lg:px-12 xl:w-8/12 xl:px-20"
        >
          Integrate your AI with 5566 skills and extensions built by the community.
        </Typography>
        <div className="grid place-items-start justify-center gap-2">
          <div className="mt-8 flex flex-col items-center justify-center gap-4 md:flex-row">
            <div className="w-80">
              {/* @ts-ignore */}
              <Input label="find your mcp server" color="white" className="bg-gray-800 text-white" labelProps={{className: '!text-gray-400'}} />
            </div>
            <Button size="md" className="lg:w-max shrink-0" fullWidth color="white">
              Search
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
export default Hero;
